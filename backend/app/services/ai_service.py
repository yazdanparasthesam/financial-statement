"""Every LLM call goes through here: LangChain providers, LangGraph agent patterns,
redaction, and ai_requests logging (security/ai-data-policy.md).

Agent patterns (see infra/ai/graphs.py):
- call_ai          — single-shot completion (anomaly explain, mapping suggest)
- run_notes_draft  — Self-criticism graph: draft → critique → bounded revise loop
- run_chat         — ReAct agent: tool-calling loop over read-only filing tools
- run_audit_memo   — ReWOO graph: plan → execute tools → solve into a memo

Failures never propagate: callers get an '[AI UNAVAILABLE]' string and the
attempt is logged with status='error'. Deterministic reports are unaffected.
"""
import time
from collections.abc import Callable
from datetime import date

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..config import get_settings
from ..infra.ai import graphs, prompts
from ..infra.ai.providers import get_chat_model, model_name, prompt_hash, provider_name
from ..infra.telemetry import observe_ai_call
from . import pipeline

# Redaction: never ship identifiers to an external model (see security/ai-data-policy.md)
REDACT_KEYS = ("national_id", "economic_code", "email")


def redact(context: dict) -> dict:
    return {k: ("[REDACTED]" if k in REDACT_KEYS else v) for k, v in context.items()}


def _log(db: Session, *, kind: str, llm, settings, hash_input: str, status: str,
         latency_ms: int, filing_id: int | None) -> None:
    db.add(models.AIRequest(
        filing_id=filing_id, kind=kind, provider=provider_name(llm),
        model=model_name(llm, settings), prompt_hash=prompt_hash(hash_input),
        status=status, latency_ms=latency_ms,
    ))
    observe_ai_call(kind, provider_name(llm), status, latency_ms / 1000.0)


def provider_name_str() -> str:
    """Provider the settings would select — for error paths without an llm object."""
    settings = get_settings()
    return provider_name(get_chat_model(settings))


# ---------------------------------------------------------------- single-shot

def call_ai(db: Session, *, kind: str, system: str, user: str,
            filing_id: int | None = None) -> tuple[str, str]:
    """Returns (text, provider_name). Logs every attempt to ai_requests."""
    settings = get_settings()
    llm = get_chat_model(settings)
    t0 = time.monotonic()
    status = "ok"
    try:
        resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        text = resp.content if isinstance(resp.content, str) else str(resp.content)
    except Exception:  # noqa: BLE001 — fail-open: degrade to '[AI UNAVAILABLE]', never 500
        status = "error"
        text = ("[AI UNAVAILABLE] The model provider could not be reached. The deterministic "
                "reports (statements, validations) are unaffected; retry the AI action later.")
    _log(db, kind=kind, llm=llm, settings=settings, hash_input=system + user, status=status,
         latency_ms=int((time.monotonic() - t0) * 1000), filing_id=filing_id)
    return text, provider_name(llm)


# ---------------------------------------------------------------- self-criticism

def run_notes_draft(db: Session, *, section: str, context: str, validations: str,
                    filing_id: int | None = None) -> tuple[str, list, str]:
    """Notes drafting as a LangGraph reflection loop. Returns (final_text, trace, provider)."""
    settings = get_settings()
    llm = get_chat_model(settings)
    t0 = time.monotonic()
    status = "ok"
    try:
        graph = graphs.build_notes_graph(llm, settings.ai_max_critique_loops)
        out = graph.invoke(graphs.notes_initial_state(section, context, validations))
        text, trace = out["final"], out["trace"]
    except Exception:  # noqa: BLE001 — fail-open: degrade to '[AI UNAVAILABLE]', never 500
        status = "error"
        text, trace = "[AI UNAVAILABLE] Note drafting failed; the section data is unaffected.", []
    _log(db, kind="notes_draft", llm=llm, settings=settings, hash_input=section + context,
         status=status, latency_ms=int((time.monotonic() - t0) * 1000), filing_id=filing_id)
    return text, trace, provider_name(llm)


# ---------------------------------------------------------------- ReAct chat

def run_chat(db: Session, *, message: str, context_text: str, filing: models.Filing,
             filing_id: int | None = None) -> tuple[str, str]:
    """Assistant chat as a LangGraph ReAct agent over read-only filing tools."""
    settings = get_settings()
    llm = get_chat_model(settings)
    t0 = time.monotonic()
    status = "ok"
    try:
        agent = graphs.build_assistant_agent(
            llm, as_langchain_tools(tools_registry(db, filing)),
            prompts.ASSISTANT_SYSTEM + f"\n\nFiling context (already fetched):\n{context_text}",
        )
        out = agent.invoke({"messages": [HumanMessage(content=message)]})
        text = out["messages"][-1].content
        if not isinstance(text, str):
            text = str(text)
    except Exception:  # noqa: BLE001 — fail-open: degrade to '[AI UNAVAILABLE]', never 500
        status = "error"
        text = ("[AI UNAVAILABLE] The assistant could not answer right now. The deterministic "
                "reports (statements, ratios, validations, checklist) remain fully available.")
    _log(db, kind="chat", llm=llm, settings=settings, hash_input=context_text + message,
         status=status, latency_ms=int((time.monotonic() - t0) * 1000), filing_id=filing_id)
    return text, provider_name(llm)


# ---------------------------------------------------------------- ReWOO audit

def run_audit_memo(db: Session, *, context_text: str, registry: dict[str, Callable[[], str]],
                   filing_id: int | None = None) -> tuple[str, list, list, str]:
    """Audit memo as a LangGraph ReWOO workflow: plan → execute → solve."""
    settings = get_settings()
    llm = get_chat_model(settings)
    t0 = time.monotonic()
    status = "ok"
    try:
        graph = graphs.build_audit_graph(llm, registry)
        out = graph.invoke(graphs.audit_initial_state(context_text))
        memo, plan, observations = out["memo"], out["plan"], out["observations"]
    except Exception:  # noqa: BLE001 — fail-open: degrade to '[AI UNAVAILABLE]', never 500
        status = "error"
        memo, plan, observations = "[AI UNAVAILABLE] Audit memo generation failed.", [], []
    _log(db, kind="audit_memo", llm=llm, settings=settings, hash_input=context_text,
         status=status, latency_ms=int((time.monotonic() - t0) * 1000), filing_id=filing_id)
    return memo, plan, observations, provider_name(llm)


# ---------------------------------------------------------------- read-only tools

def _validations_text(db: Session, filing_id: int) -> str:
    run = db.scalar(select(models.ValidationRun).where(models.ValidationRun.filing_id == filing_id)
                    .order_by(models.ValidationRun.id.desc()))
    if run is None:
        return "Validation has not been run yet."
    results = db.scalars(select(models.ValidationResult)
                         .where(models.ValidationResult.run_id == run.id)).all()
    return (f"Validation run #{run.id}: passed={run.passed} failed={run.failed}\n"
            + "\n".join(f"[{'PASS' if r.passed else 'FAIL'}|{r.severity}|{r.rule_id}] {r.message}"
                        for r in results))


def _anomalies_text(db: Session, filing_id: int) -> str:
    rows = db.scalars(select(models.Anomaly).where(
        models.Anomaly.filing_id == filing_id, models.Anomaly.dismissed == False)).all()  # noqa: E712
    if not rows:
        return "No year-over-year anomalies detected."
    return "\n".join(
        f"{a.account_code} ({a.account_name}): prior={a.prior_value:,.0f} "
        f"current={a.current_value:,.0f} change={a.pct_change}%"
        + (f" — explanation: {a.ai_explanation}" if a.ai_explanation else " (no explanation yet)")
        for a in rows)


def _checklist_text(db: Session, filing: models.Filing) -> str:
    items = pipeline.build_checklist(db, filing)
    done = sum(1 for i in items if i["done"])
    return (f"Checklist {done}/{len(items)} done:\n"
            + "\n".join(f"- [{'x' if i['done'] else ' '}] {i['item']}" for i in items))


def _deadline_text(filing: models.Filing) -> str:
    if not filing.deadline:
        return "No deadline recorded for this filing."
    d = date.fromisoformat(filing.deadline)
    days = (d - date.today()).days
    status = "upcoming" if days > 30 else ("approaching" if days >= 0 else "overdue")
    return (f"Statutory deadline {filing.deadline} (Art.95: FY end + 4 months); "
            f"{days} days remaining; status={status}")


def _ratios_text(db: Session, filing_id: int) -> str:
    try:
        rs = pipeline.compute_ratios(db, filing_id)
    except Exception:  # noqa: BLE001 — fail-open: degrade to '[AI UNAVAILABLE]', never 500
        return "No ratios available — generate statements first."
    return "\n".join(f"{r['label']} = {r['value']} {r['unit']} ({r['formula']})" for r in rs)


def tools_registry(db: Session, filing: models.Filing) -> dict[str, tuple[str, Callable[[], str]]]:
    """Read-only filing tools: name → (description, zero-arg deterministic callable).

    Tools never write and never invent figures — they serialize domain output."""
    fid = filing.id
    return {
        "get_statements_summary": (
            "Deterministic text summary of the latest P&L and balance sheet figures.",
            lambda: pipeline.statements_summary(db, fid)),
        "get_validation_report": (
            "Latest validation run: PASS/FAIL lines per rule with severity and message.",
            lambda: _validations_text(db, fid)),
        "get_anomalies": (
            "Open year-over-year anomalies with percentages and any AI explanations.",
            lambda: _anomalies_text(db, fid)),
        "get_checklist": (
            "Filing checklist items and their done-state.",
            lambda: _checklist_text(db, filing)),
        "get_deadline": (
            "Statutory deadline (Art.95), days remaining and status.",
            lambda: _deadline_text(filing)),
        "get_ratios": (
            "Financial ratios with formula strings (current, quick, D/E, margins, ROE, ROA, EBITDA).",
            lambda: _ratios_text(db, fid)),
    }


def as_langchain_tools(registry: dict[str, tuple[str, Callable[[], str]]]) -> list:
    from langchain_core.tools import StructuredTool
    return [StructuredTool.from_function(func=fn, name=name, description=desc)
            for name, (desc, fn) in registry.items()]
