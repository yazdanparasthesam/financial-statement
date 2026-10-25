"""AI endpoints: anomaly explanations, notes drafting, grounded chat.
Every call is logged to ai_requests; identifiers are redacted (ai_service.redact)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import ensure_access, get_current_user, get_filing_or_404
from ..infra.ai import prompts
from ..services import pipeline
from ..services.ai_service import call_ai, redact, run_audit_memo, run_chat, run_notes_draft, tools_registry
from ..services.audit import log_event

router = APIRouter(tags=["ai"])


def _validations_summary(db: Session, filing_id: int) -> str:
    run = db.scalar(select(models.ValidationRun).where(models.ValidationRun.filing_id == filing_id)
                    .order_by(models.ValidationRun.id.desc()))
    if run is None:
        return "Validation has not been run yet."
    results = db.scalars(select(models.ValidationResult)
                         .where(models.ValidationResult.run_id == run.id)).all()
    return "\n".join(f"[{'PASS' if r.passed else 'FAIL'}|{r.severity}|{r.rule_id}] {r.message}"
                     for r in results)


@router.post("/api/anomalies/{anomaly_id}/explain", response_model=schemas.ExplainOut)
def explain_anomaly(anomaly_id: int, db: Session = Depends(get_db),
                    user: models.User = Depends(get_current_user)):
    anomaly = db.get(models.Anomaly, anomaly_id)
    if anomaly is None:
        raise HTTPException(404, "Anomaly not found")
    filing = get_filing_or_404(db, anomaly.filing_id)
    ensure_access(db, filing, user, write=True)
    adict = {"account_code": anomaly.account_code, "account_name": anomaly.account_name,
             "prior_value": anomaly.prior_value, "current_value": anomaly.current_value,
             "pct_change": anomaly.pct_change}
    system, up = prompts.anomaly_explain(adict, pipeline.statements_summary(db, filing.id))
    text, provider = call_ai(db, kind="anomaly_explain", system=system, user=up, filing_id=filing.id)
    anomaly.ai_explanation = text
    log_event(db, actor_id=user.id, action="ai.anomaly_explain", entity="anomaly", entity_id=anomaly.id)
    db.commit()
    return schemas.ExplainOut(anomaly_id=anomaly.id, explanation=text, provider=provider)


@router.post("/api/filings/{filing_id}/notes/draft", response_model=schemas.NoteOut)
def draft_note(filing_id: int, body: schemas.NoteDraftIn, db: Session = Depends(get_db),
               user: models.User = Depends(get_current_user)):
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user, write=True)
    section = body.section.strip().lower().replace(" ", "_")
    allowed = ("revenue", "cogs", "operating_expenses", "other_income", "other_expenses",
               "tax_expense", "current_assets", "non_current_assets", "current_liabilities",
               "non_current_liabilities", "equity", "general")
    if section not in allowed:
        raise HTTPException(400, f"section must be one of: {', '.join(allowed)}")
    # Self-criticism graph: draft -> critique -> bounded revise loop -> finalize.
    text, trace, provider = run_notes_draft(
        db, section=section,
        context=pipeline.statements_summary(db, filing_id),
        validations=_validations_summary(db, filing_id),
        filing_id=filing_id)
    loops = sum(1 for s in trace if s["step"] == "revise")
    note = db.scalar(select(models.StatementNote).where(
        models.StatementNote.filing_id == filing_id, models.StatementNote.section == section))
    if note is None:
        note = models.StatementNote(filing_id=filing_id, section=section)
        db.add(note)
    note.draft_text = text
    note.ai_generated = True
    log_event(db, actor_id=user.id, action="ai.notes_draft", entity="filing", entity_id=filing_id,
              detail={"section": section, "provider": provider, "pattern": "self-criticism",
                      "trace_steps": len(trace), "revise_loops": loops})
    db.commit()
    return note


@router.get("/api/filings/{filing_id}/notes", response_model=list[schemas.NoteOut])
def list_notes(filing_id: int, db: Session = Depends(get_db),
               user: models.User = Depends(get_current_user)):
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user)
    return db.scalars(select(models.StatementNote).where(models.StatementNote.filing_id == filing_id)
                      .order_by(models.StatementNote.id)).all()


@router.patch("/api/notes/{note_id}", response_model=schemas.NoteOut)
def finalize_note(note_id: int, body: schemas.NoteUpdate, db: Session = Depends(get_db),
                  user: models.User = Depends(get_current_user)):
    note = db.get(models.StatementNote, note_id)
    if note is None:
        raise HTTPException(404, "Note not found")
    filing = get_filing_or_404(db, note.filing_id)
    ensure_access(db, filing, user, write=True)
    note.final_text = body.final_text
    log_event(db, actor_id=user.id, action="notes.finalize", entity="note", entity_id=note.id)
    db.commit()
    return note


@router.post("/api/filings/{filing_id}/assistant/chat", response_model=schemas.ChatOut)
def chat(filing_id: int, body: schemas.ChatIn, db: Session = Depends(get_db),
         user: models.User = Depends(get_current_user)):
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user)
    company = db.get(models.Company, filing.company_id)
    context = redact({
        "company_name": company.name if company else "?",
        "national_id": company.national_id if company else "",
        "fiscal_year": filing.fiscal_year,
        "status": filing.status,
        "deadline": filing.deadline,
        "statements": pipeline.statements_summary(db, filing_id),
        "validations": _validations_summary(db, filing_id),
    })
    ctx_text = "\n".join(f"{k}: {v}" for k, v in context.items())
    # ReAct agent: the model may call the read-only filing tools before answering.
    text, provider = run_chat(db, message=body.message, context_text=ctx_text,
                              filing=filing, filing_id=filing_id)
    db.commit()
    return schemas.ChatOut(reply=text, provider=provider)


@router.post("/api/filings/{filing_id}/audit-memo", response_model=schemas.AuditMemoOut)
def audit_memo(filing_id: int, db: Session = Depends(get_db),
               user: models.User = Depends(get_current_user)):
    """ReWOO audit memo: planner builds a tool plan, executor runs the read-only
    tools, solver synthesizes the memo. Every figure comes from deterministic code."""
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user)
    company = db.get(models.Company, filing.company_id)
    context = redact({
        "company_name": company.name if company else "?",
        "national_id": company.national_id if company else "",
        "fiscal_year": filing.fiscal_year,
        "status": filing.status,
        "deadline": filing.deadline,
    })
    ctx_text = "\n".join(f"{k}: {v}" for k, v in context.items())
    registry = {name: fn for name, (_desc, fn) in tools_registry(db, filing).items()}
    memo, plan, observations, provider = run_audit_memo(
        db, context_text=ctx_text, registry=registry, filing_id=filing_id)
    log_event(db, actor_id=user.id, action="ai.audit_memo", entity="filing", entity_id=filing_id,
              detail={"provider": provider, "pattern": "rewoo",
                      "plan": plan, "observations": len(observations)})
    db.commit()
    return schemas.AuditMemoOut(memo=memo, plan=plan,
                                observations_count=len(observations), provider=provider)
