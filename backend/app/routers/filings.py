from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import get_settings
from ..db import get_db
from ..deps import ensure_access, get_current_user, get_filing_or_404
from ..domain.deadlines import days_remaining, filing_deadline
from ..services.audit import log_event

router = APIRouter(prefix="/api/filings", tags=["filings"])


def _own_company_ids(db: Session, user: models.User) -> list[int]:
    return list(db.scalars(select(models.Company.id).where(models.Company.owner_id == user.id)))


@router.post("", response_model=schemas.FilingOut, status_code=201)
def create_filing(body: schemas.FilingCreate, db: Session = Depends(get_db),
                  user: models.User = Depends(get_current_user)):
    company = db.get(models.Company, body.company_id)
    if company is None:
        raise HTTPException(404, "Company not found")
    if company.owner_id != user.id:
        raise HTTPException(403, "Only the company owner can create filings")
    exists = db.scalar(select(models.Filing).where(
        models.Filing.company_id == body.company_id, models.Filing.fiscal_year == body.fiscal_year))
    if exists:
        raise HTTPException(409, f"A filing for fiscal year {body.fiscal_year} already exists (id {exists.id})")
    s = get_settings()
    deadline = filing_deadline(body.fiscal_year, company.fiscal_year_end_month, s.filing_deadline_months)
    filing = models.Filing(company_id=body.company_id, fiscal_year=body.fiscal_year,
                           deadline=deadline.isoformat())
    db.add(filing)
    db.flush()
    log_event(db, actor_id=user.id, action="filing.create", entity="filing", entity_id=filing.id,
              detail={"fiscal_year": filing.fiscal_year, "deadline": filing.deadline})
    db.commit()
    return filing


@router.get("", response_model=list[schemas.FilingOut])
def list_filings(company_id: int | None = None, status: str | None = None,
                 db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    q = select(models.Filing)
    if user.role != "reviewer":
        q = q.where(models.Filing.company_id.in_(_own_company_ids(db, user) or [-1]))
    if company_id is not None:
        q = q.where(models.Filing.company_id == company_id)
    if status is not None:
        q = q.where(models.Filing.status == status)
    return db.scalars(q.order_by(models.Filing.id.desc())).all()


@router.get("/{filing_id}", response_model=schemas.FilingOut)
def get_filing(filing_id: int, db: Session = Depends(get_db),
               user: models.User = Depends(get_current_user)):
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user)
    return filing


@router.get("/{filing_id}/deadline", response_model=schemas.DeadlineOut)
def get_deadline(filing_id: int, db: Session = Depends(get_db),
                 user: models.User = Depends(get_current_user)):
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user)
    d = date.fromisoformat(filing.deadline) if filing.deadline else None
    return schemas.DeadlineOut(fiscal_year=filing.fiscal_year, deadline=filing.deadline,
                               days_remaining=days_remaining(d) if d else -1)
