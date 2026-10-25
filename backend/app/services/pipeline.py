"""Orchestration: generate statements, run validation, build checklist. Routers stay thin."""
import time

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..config import get_settings
from ..domain import cashflow, generator, validators
from ..domain import ratios as ratios_domain
from ..infra.telemetry import inc_statement, inc_validation, observe_journey_step
from .audit import log_event


def accounts_as_dicts(db: Session, filing_id: int) -> tuple[list[dict], models.TrialBalance]:
    tb = db.scalar(select(models.TrialBalance).where(models.TrialBalance.filing_id == filing_id))
    if tb is None:
        raise HTTPException(400, "No trial balance uploaded for this filing yet.")
    rows = db.scalars(select(models.TBAccount).where(models.TBAccount.tb_id == tb.id)).all()
    return [
        {"code": r.code, "name": r.name, "debit": r.debit, "credit": r.credit,
         "category": r.category if r.mapping_status == "mapped" else ""}
        for r in rows
    ], tb


def latest_statement(db: Session, filing_id: int, kind: str) -> models.Statement | None:
    return db.scalar(
        select(models.Statement)
        .where(models.Statement.filing_id == filing_id, models.Statement.kind == kind)
        .order_by(models.Statement.version.desc())
    )


def prior_year_statements(db: Session, filing: models.Filing) -> dict[str, dict] | None:
    """Prior fiscal year's latest pl+bs for the same company, or None."""
    prior = db.scalar(select(models.Filing).where(
        models.Filing.company_id == filing.company_id,
        models.Filing.fiscal_year == filing.fiscal_year - 1))
    if prior is None:
        return None
    ppl, pbs = latest_statement(db, prior.id, "pl"), latest_statement(db, prior.id, "bs")
    if ppl and pbs:
        return {"pl": ppl.data, "bs": pbs.data}
    return None


def generate_statements(db: Session, filing: models.Filing, actor_id: int) -> dict[str, models.Statement]:
    t0 = time.monotonic()
    accounts, _tb = accounts_as_dicts(db, filing.id)
    data = generator.build_statements(accounts)

    # cash-flow (indirect method) when a prior-year balance sheet exists
    prior = prior_year_statements(db, filing)
    cf = cashflow.build_cash_flow(data["pl"], data["bs"], prior["bs"]) if prior else None
    if cf is not None:
        data["cf"] = cf

    out = {}
    for kind in ("pl", "bs", "cf") if cf is not None else ("pl", "bs"):
        prev = latest_statement(db, filing.id, kind)
        version = (prev.version + 1) if prev else 1
        stmt = models.Statement(filing_id=filing.id, kind=kind, version=version, data=data[kind])
        db.add(stmt)
        out[kind] = stmt
    log_event(db, actor_id=actor_id, action="statements.generate", entity="filing", entity_id=filing.id,
              detail={"pl_version": out["pl"].version})
    db.commit()
    for kind in out:
        inc_statement(kind)
    observe_journey_step("generate", time.monotonic() - t0)
    return out


def run_validation(db: Session, filing: models.Filing, actor_id: int) -> models.ValidationRun:
    _t_validation = time.monotonic()
    settings = get_settings()
    accounts, tb = accounts_as_dicts(db, filing.id)

    pl, bs = latest_statement(db, filing.id, "pl"), latest_statement(db, filing.id, "bs")
    statements = {"pl": pl.data, "bs": bs.data} if pl and bs else None

    # prior-year statements for YoY anomalies (same company, fiscal_year - 1)
    prior_statements = prior_year_statements(db, filing)

    cf_stmt = latest_statement(db, filing.id, "cf")
    outcome = validators.run_rules(
        tb_total_debit=tb.total_debit, tb_total_credit=tb.total_credit,
        accounts=accounts, statements=statements, prior_statements=prior_statements,
        threshold_pct=settings.anomaly_pct_threshold,
        cash_flow=cf_stmt.data if cf_stmt else None,
    )

    run = models.ValidationRun(filing_id=filing.id,
                               passed=sum(1 for r in outcome.results if r.passed),
                               failed=sum(1 for r in outcome.results if not r.passed))
    db.add(run)
    db.flush()
    for r in outcome.results:
        db.add(models.ValidationResult(run_id=run.id, rule_id=r.rule_id, severity=r.severity,
                                       passed=r.passed, message=r.message, context=r.context))
    # replace open anomalies with fresh scan
    for old in db.scalars(select(models.Anomaly).where(
            models.Anomaly.filing_id == filing.id, models.Anomaly.dismissed == False)):  # noqa: E712
        db.delete(old)
    for a in outcome.anomalies:
        db.add(models.Anomaly(filing_id=filing.id, **a))
    log_event(db, actor_id=actor_id, action="validation.run", entity="filing", entity_id=filing.id,
              detail={"passed": run.passed, "failed": run.failed, "anomalies": len(outcome.anomalies)})
    db.commit()
    inc_validation(run.failed)
    observe_journey_step("validate", time.monotonic() - _t_validation)
    return run


def build_checklist(db: Session, filing: models.Filing) -> list[dict]:
    tb = db.scalar(select(models.TrialBalance).where(models.TrialBalance.filing_id == filing.id))
    accounts_mapped = True
    if tb is not None:
        accounts_mapped = db.scalar(select(models.TBAccount).where(
            models.TBAccount.tb_id == tb.id, models.TBAccount.mapping_status == "unmapped").limit(1)) is None
    run = db.scalar(select(models.ValidationRun).where(models.ValidationRun.filing_id == filing.id)
                    .order_by(models.ValidationRun.run_at.desc()))
    notes = db.scalars(select(models.StatementNote).where(
        models.StatementNote.filing_id == filing.id, models.StatementNote.final_text != "")).all()
    from datetime import date

    deadline_ok = bool(filing.deadline) and date.fromisoformat(filing.deadline) >= date.today()
    return [
        {"item": "Trial balance uploaded", "done": tb is not None},
        {"item": "All accounts mapped to statutory categories", "done": bool(tb) and accounts_mapped},
        {"item": "P&L and Balance Sheet generated",
         "done": bool(latest_statement(db, filing.id, "pl")
                      and latest_statement(db, filing.id, "bs"))},
        {"item": "Validation run with zero failed error-rules", "done": bool(run and run.failed == 0)},
        {"item": "Notes to the accounts finalized", "done": len(notes) >= 2},
        {"item": "Submitted for review", "done": filing.status in ("submitted", "in_review", "accepted")},
        {"item": "Accepted by reviewer", "done": filing.status == "accepted"},
        {"item": f"Within statutory deadline ({filing.deadline or 'n/a'})", "done": deadline_ok},
    ]


def statements_summary(db: Session, filing_id: int) -> str:
    """Compact text summary of the current statements — grounding context for the LLM."""
    pl, bs = latest_statement(db, filing_id, "pl"), latest_statement(db, filing_id, "bs")
    if not pl or not bs:
        return "No statements generated yet."
    p, b = pl.data, bs.data
    return (
        f"P&L: revenue {p['revenue']['total']:,.0f}; COGS {p['cogs']['total']:,.0f}; "
        f"gross profit {p['gross_profit']:,.0f}; opex {p['operating_expenses']['total']:,.0f}; "
        f"operating profit {p['operating_profit']:,.0f}; other income {p['other_income']['total']:,.0f}; "
        f"other expenses {p['other_expenses']['total']:,.0f}; tax {p['tax_expense']['total']:,.0f}; "
        f"net profit {p['net_profit']:,.0f}.\n"
        f"BS: current assets {b['current_assets']['total']:,.0f}; non-current assets "
        f"{b['non_current_assets']['total']:,.0f}; total assets {b['total_assets']:,.0f}; "
        f"current liabilities {b['current_liabilities']['total']:,.0f}; non-current liabilities "
        f"{b['non_current_liabilities']['total']:,.0f}; equity (incl. current-year profit "
        f"{b['current_year_profit']:,.0f}) {b['total_equity']:,.0f}; L+E {b['total_liabilities_and_equity']:,.0f}."
    )


def compute_ratios(db: Session, filing_id: int) -> list[dict]:
    """Deterministic ratios with formula strings (domain/ratios.py)."""
    pl, bs = latest_statement(db, filing_id, "pl"), latest_statement(db, filing_id, "bs")
    if not pl or not bs:
        raise HTTPException(404, "Generate statements first — ratios need the P&L and balance sheet.")
    accounts, _tb = accounts_as_dicts(db, filing_id)
    return ratios_domain.scale_percentages(
        ratios_domain.compute_ratios(pl.data, bs.data, accounts))
