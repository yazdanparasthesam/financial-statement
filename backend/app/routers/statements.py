from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import ensure_access, get_current_user, get_filing_or_404
from ..services import pipeline

router = APIRouter(prefix="/api/filings/{filing_id}/statements", tags=["statements"])


@router.post("/generate", response_model=list[schemas.StatementOut], status_code=201)
def generate(filing_id: int, db: Session = Depends(get_db),
             user: models.User = Depends(get_current_user)):
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user, write=True)
    if filing.status not in ("draft", "changes_requested"):
        raise HTTPException(422, f"Cannot regenerate statements while filing is '{filing.status}'")
    out = pipeline.generate_statements(db, filing, user.id)
    return [out["pl"], out["bs"]]


@router.get("/{kind}", response_model=schemas.StatementOut)
def get_statement(filing_id: int, kind: str, db: Session = Depends(get_db),
                  user: models.User = Depends(get_current_user)):
    if kind not in ("pl", "bs", "cf"):
        raise HTTPException(400, "kind must be 'pl', 'bs' or 'cf'")
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user)
    stmt = pipeline.latest_statement(db, filing_id, kind)
    if stmt is None:
        raise HTTPException(404, f"No {kind} statement generated yet")
    return stmt
