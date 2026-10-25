import time

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import ensure_access, get_current_user, get_filing_or_404
from ..domain.mapping import ALL_CATEGORIES, auto_map, is_valid_category
from ..infra.ai import prompts
from ..infra.ai.providers import parse_mapping_suggestions
from ..infra.ingestion import parse_trial_balance
from ..infra.telemetry import observe_journey_step
from ..services.ai_service import call_ai
from ..services.audit import log_event

router = APIRouter(prefix="/api/filings/{filing_id}/trial-balance", tags=["trial-balance"])


def _load(db: Session, filing_id: int) -> tuple[models.TrialBalance, list[models.TBAccount]]:
    tb = db.scalar(select(models.TrialBalance).where(models.TrialBalance.filing_id == filing_id))
    if tb is None:
        raise HTTPException(404, "No trial balance uploaded for this filing")
    rows = db.scalars(select(models.TBAccount).where(models.TBAccount.tb_id == tb.id)
                      .order_by(models.TBAccount.id)).all()
    return tb, list(rows)


@router.post("", response_model=schemas.TrialBalanceOut)
async def upload_trial_balance(filing_id: int, file: UploadFile, db: Session = Depends(get_db),
                               user: models.User = Depends(get_current_user)):
    t0 = time.monotonic()
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user, write=True)
    if filing.status not in ("draft", "changes_requested"):
        raise HTTPException(422, f"Cannot modify trial balance while filing is '{filing.status}'")
    content = await file.read()
    rows = parse_trial_balance(file.filename or "upload.csv", content)

    # replace any previous import (statement versions keep the history)
    old = db.scalar(select(models.TrialBalance).where(models.TrialBalance.filing_id == filing_id))
    if old is not None:
        for r in db.scalars(select(models.TBAccount).where(models.TBAccount.tb_id == old.id)):
            db.delete(r)
        db.delete(old)
        db.flush()

    tb = models.TrialBalance(filing_id=filing_id, source_filename=file.filename or "upload.csv",
                             total_debit=round(sum(r["debit"] for r in rows), 2),
                             total_credit=round(sum(r["credit"] for r in rows), 2))
    db.add(tb)
    db.flush()
    for r in rows:
        category = auto_map(r["code"], r["name"])
        db.add(models.TBAccount(tb_id=tb.id, code=r["code"], name=r["name"],
                                debit=r["debit"], credit=r["credit"],
                                category=category or "",
                                mapping_status="mapped" if category else "unmapped"))
    log_event(db, actor_id=user.id, action="tb.upload", entity="filing", entity_id=filing_id,
              detail={"rows": len(rows), "total_debit": tb.total_debit, "total_credit": tb.total_credit})
    db.commit()
    observe_journey_step("upload", time.monotonic() - t0)
    tb2, accounts = _load(db, filing_id)
    return schemas.TrialBalanceOut(
        id=tb2.id, source_filename=tb2.source_filename, total_debit=tb2.total_debit,
        total_credit=tb2.total_credit, imported_at=tb2.imported_at,
        accounts=[schemas.TBAccountOut.model_validate(a) for a in accounts])


@router.get("", response_model=schemas.TrialBalanceOut)
def get_trial_balance(filing_id: int, db: Session = Depends(get_db),
                      user: models.User = Depends(get_current_user)):
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user)
    tb, accounts = _load(db, filing_id)
    return schemas.TrialBalanceOut(
        id=tb.id, source_filename=tb.source_filename, total_debit=tb.total_debit,
        total_credit=tb.total_credit, imported_at=tb.imported_at,
        accounts=[schemas.TBAccountOut.model_validate(a) for a in accounts])


@router.patch("/accounts/{account_id}", response_model=schemas.TBAccountOut)
def update_mapping(filing_id: int, account_id: int, body: schemas.MappingUpdate,
                   db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user, write=True)
    if not is_valid_category(body.category):
        raise HTTPException(400, f"Unknown category '{body.category}'. Valid: {', '.join(ALL_CATEGORIES)}")
    account = db.get(models.TBAccount, account_id)
    if account is None:
        raise HTTPException(404, "Account not found")
    tb, _ = _load(db, filing_id)
    if account.tb_id != tb.id:
        raise HTTPException(400, "Account does not belong to this filing's trial balance")
    account.category = body.category
    account.mapping_status = "mapped"
    log_event(db, actor_id=user.id, action="tb.map", entity="tb_account", entity_id=account.id,
              detail={"code": account.code, "category": body.category})
    db.commit()
    return account


@router.post("/suggest-mappings", response_model=list[schemas.MappingSuggestion])
def suggest_mappings(filing_id: int, db: Session = Depends(get_db),
                     user: models.User = Depends(get_current_user)):
    """AI suggests categories for unmapped accounts — suggestions only; a human applies them."""
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user, write=True)
    _tb, accounts = _load(db, filing_id)
    unmapped = [{"code": a.code, "name": a.name, "debit": a.debit, "credit": a.credit}
                for a in accounts if a.mapping_status == "unmapped"]
    if not unmapped:
        return []
    system, user_prompt = prompts.mapping_suggest(unmapped)
    text, _provider = call_ai(db, kind="mapping_suggest", system=system, user=user_prompt,
                              filing_id=filing_id)
    by_code = {a.code: a for a in accounts}
    out = []
    for s in parse_mapping_suggestions(text):
        account = by_code.get(s["code"])
        if account and is_valid_category(s["suggested_category"]):
            out.append(schemas.MappingSuggestion(account_id=account.id, code=account.code,
                                                 name=account.name,
                                                 suggested_category=s["suggested_category"],
                                                 reason=s["reason"]))
    db.commit()  # persist ai_requests log row
    return out
