from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import get_current_user
from ..services.audit import log_event

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.post("", response_model=schemas.CompanyOut, status_code=201)
def create_company(body: schemas.CompanyCreate, db: Session = Depends(get_db),
                   user: models.User = Depends(get_current_user)):
    company = models.Company(**body.model_dump(), owner_id=user.id)
    db.add(company)
    db.flush()
    log_event(db, actor_id=user.id, action="company.create", entity="company", entity_id=company.id)
    db.commit()
    return company


@router.get("", response_model=list[schemas.CompanyOut])
def list_companies(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    q = select(models.Company)
    if user.role != "reviewer":
        q = q.where(models.Company.owner_id == user.id)
    return db.scalars(q.order_by(models.Company.id)).all()


@router.get("/{company_id}", response_model=schemas.CompanyOut)
def get_company(company_id: int, db: Session = Depends(get_db),
                user: models.User = Depends(get_current_user)):
    company = db.get(models.Company, company_id)
    if company is None:
        raise HTTPException(404, "Company not found")
    if user.role != "reviewer" and company.owner_id != user.id:
        raise HTTPException(403, "No access to this company")
    return company
