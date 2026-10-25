from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import ensure_access, get_current_user, get_filing_or_404
from ..services import pipeline

router = APIRouter(prefix="/api/filings/{filing_id}", tags=["validation"])


def _run_out(db: Session, run: models.ValidationRun) -> schemas.ValidationRunOut:
    results = db.scalars(select(models.ValidationResult)
                         .where(models.ValidationResult.run_id == run.id)
                         .order_by(models.ValidationResult.id)).all()
    return schemas.ValidationRunOut(
        id=run.id, run_at=run.run_at, passed=run.passed, failed=run.failed,
        results=[schemas.ValidationResultOut(rule_id=r.rule_id, severity=r.severity,
                                             passed=r.passed, message=r.message, context=r.context)
                 for r in results])


@router.post("/validate", response_model=schemas.ValidationRunOut)
def validate(filing_id: int, db: Session = Depends(get_db),
             user: models.User = Depends(get_current_user)):
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user, write=True)
    run = pipeline.run_validation(db, filing, user.id)
    return _run_out(db, run)


@router.get("/validations/latest", response_model=schemas.ValidationRunOut)
def latest(filing_id: int, db: Session = Depends(get_db),
           user: models.User = Depends(get_current_user)):
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user)
    run = db.scalar(select(models.ValidationRun).where(models.ValidationRun.filing_id == filing_id)
                    .order_by(models.ValidationRun.run_at.desc(), models.ValidationRun.id.desc()))
    if run is None:
        raise HTTPException(404, "Validation has not been run yet")
    return _run_out(db, run)


@router.get("/ratios", response_model=list[schemas.RatioOut], tags=["statements"])
def ratios(filing_id: int, db: Session = Depends(get_db),
           user: models.User = Depends(get_current_user)):
    """Financial ratios with their formulas — computed by domain code, never by the AI."""
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user)
    return pipeline.compute_ratios(db, filing_id)


@router.get("/anomalies", response_model=list[schemas.AnomalyOut])
def anomalies(filing_id: int, include_dismissed: bool = False, db: Session = Depends(get_db),
              user: models.User = Depends(get_current_user)):
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user)
    q = select(models.Anomaly).where(models.Anomaly.filing_id == filing_id)
    if not include_dismissed:
        q = q.where(models.Anomaly.dismissed == False)  # noqa: E712
    return db.scalars(q.order_by(models.Anomaly.id)).all()
