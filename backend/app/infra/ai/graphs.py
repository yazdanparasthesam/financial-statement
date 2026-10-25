"""LangGraph workflows — the three agent patterns, offline-safe.

1. Self-criticism (reflection): draft → critique → conditional revise loop
   (bounded by settings.ai_max_critique_loops) → finalize. Used for note drafting.
2. ReAct: langgraph.prebuilt.create_react_agent over read-only filing tools.
   Used for the assistant chat.
3. ReWOO: planner → executor loop (one tool per planned step) → solver.
   Used for the audit memo.

Every node calls the LLM through LangChain, so swapping MockChatModel for
ChatGoogleGenerativeAI changes behaviour, not structure.
"""
import json
import re
from collections.abc import Callable
from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from . import prompts as P


class NoteState(TypedDict, total=False):
    section: str
    context: str
    validations: str
    draft: str
    critique: dict
    loops: int
    final: str
    trace: list


class AuditState(TypedDict, total=False):
    context: str
    plan: list
    observations: list
    step: int
    memo: str
    trace: list


def _invoke_text(llm, system: str, user: str) -> str:
    resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
    return resp.content if isinstance(resp.content, str) else str(resp.content)


def parse_critique(text: str) -> dict:
    """Parse the critic's strict-JSON reply. Unparsable -> accept (fail-open, with a note)."""
    try:
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if m is None:
            raise ValueError("no JSON object in critique")
        data = json.loads(m.group(0))
        if not isinstance(data, dict) or "accept" not in data:
            raise ValueError("critique JSON missing 'accept'")
        return {
            "accept": bool(data["accept"]),
            "issues": [str(i) for i in data.get("issues", [])],
            "improved_draft": data.get("improved_draft") or None,
        }
    except Exception:  # noqa: BLE001 — fail-open: degrade to '[AI UNAVAILABLE]', never 500
        return {"accept": True, "issues": ["critique unparsable — accepting draft as-is"],
                "improved_draft": None}


PLAN_LINE = re.compile(r"^\s*\d+\.\s*#(\w+)", flags=re.MULTILINE)


def parse_plan(text: str) -> list[str]:
    """Numbered plan lines only: '1. #tool_a' / '2. #tool_b' -> ['tool_a', 'tool_b']."""
    return PLAN_LINE.findall(text)


# ---------------------------------------------------------------- 1) self-criticism

def build_notes_graph(llm, max_loops: int = 2):
    def draft_node(st: NoteState) -> dict:
        system, user = P.notes_draft(st["section"], st["context"], st["validations"])
        draft = _invoke_text(llm, system, user)
        return {"draft": draft,
                "trace": st["trace"] + [{"step": "draft", "loop": st["loops"], "text": draft}]}

    def critique_node(st: NoteState) -> dict:
        system, user = P.critique(st["section"], st["draft"])
        raw = _invoke_text(llm, system, user)
        return {"critique": parse_critique(raw),
                "trace": st["trace"] + [{"step": "critique", "loop": st["loops"], "text": raw}]}

    def revise_node(st: NoteState) -> dict:
        system, user = P.revise(st["section"], st["draft"], st["critique"]["issues"])
        draft = _invoke_text(llm, system, user)
        loops = st["loops"] + 1
        return {"draft": draft, "loops": loops,
                "trace": st["trace"] + [{"step": "revise", "loop": loops, "text": draft}]}

    def route_after_critique(st: NoteState) -> str:
        if st["critique"].get("accept") or st["loops"] >= max_loops:
            return "finalize"
        return "revise"

    def finalize_node(st: NoteState) -> dict:
        return {"final": st["critique"].get("improved_draft") or st["draft"]}

    g = StateGraph(NoteState)
    g.add_node("draft", draft_node)
    g.add_node("critique", critique_node)
    g.add_node("revise", revise_node)
    g.add_node("finalize", finalize_node)
    g.set_entry_point("draft")
    g.add_edge("draft", "critique")
    g.add_conditional_edges("critique", route_after_critique,
                            {"revise": "revise", "finalize": "finalize"})
    g.add_edge("revise", "critique")
    g.add_edge("finalize", END)
    return g.compile()


# ---------------------------------------------------------------- 2) ReAct assistant

def build_assistant_agent(llm, tools: list, system: str):
    """ReAct agent. Prefers the LangChain v1 API (langchain.agents.create_agent,
    built on LangGraph) and falls back to langgraph.prebuilt for older installs."""
    try:
        from langchain.agents import create_agent
        return create_agent(llm, tools, system_prompt=system)
    except ImportError:
        from langgraph.prebuilt import create_react_agent
        return create_react_agent(llm, tools, prompt=system)


# ---------------------------------------------------------------- 3) ReWOO audit

def build_audit_graph(llm, registry: dict[str, Callable[[], str]], max_steps: int = 8):
    def planner_node(st: AuditState) -> dict:
        system, user = P.rewoo_plan(st["context"], sorted(registry))
        raw = _invoke_text(llm, system, user)
        plan = [t for t in parse_plan(raw) if t in registry][:max_steps]
        return {"plan": plan, "step": 0,
                "trace": st["trace"] + [{"step": "plan", "text": raw}]}

    def route_after_plan(st: AuditState) -> str:
        return "executor" if st["plan"] and st["step"] < len(st["plan"]) else "solver"

    def executor_node(st: AuditState) -> dict:
        name = st["plan"][st["step"]]
        try:
            obs = registry[name]()
        except Exception as e:  # noqa: BLE001 — tool failure becomes an observation
            obs = f"tool error: {e}"
        return {"observations": st["observations"] + [f"[{name}] {obs}"],
                "step": st["step"] + 1,
                "trace": st["trace"] + [{"step": f"execute:{name}", "text": str(obs)[:500]}]}

    def solver_node(st: AuditState) -> dict:
        system, user = P.rewoo_solve(st["context"], st["plan"], st["observations"])
        memo = _invoke_text(llm, system, user)
        return {"memo": memo, "trace": st["trace"] + [{"step": "solve", "text": memo}]}

    g = StateGraph(AuditState)
    g.add_node("planner", planner_node)
    g.add_node("executor", executor_node)
    g.add_node("solver", solver_node)
    g.set_entry_point("planner")
    g.add_conditional_edges("planner", route_after_plan,
                            {"executor": "executor", "solver": "solver"})
    g.add_conditional_edges("executor", route_after_plan,
                            {"executor": "executor", "solver": "solver"})
    g.add_edge("solver", END)
    return g.compile()


def notes_initial_state(section: str, context: str, validations: str) -> NoteState:
    return {"section": section, "context": context, "validations": validations,
            "draft": "", "critique": {}, "loops": 0, "final": "", "trace": []}


def audit_initial_state(context: str) -> AuditState:
    return {"context": context, "plan": [], "observations": [], "step": 0,
            "memo": "", "trace": []}
