from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import ensure_access, get_current_user, get_filing_or_404
from ..infra import exports
from ..services import pipeline

router = APIRouter(prefix="/api/filings/{filing_id}", tags=["exports"])

MEDIA = {"xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
         "pdf": "application/pdf"}


def _meta(db: Session, filing: models.Filing, version) -> dict:
    company = db.get(models.Company, filing.company_id)
    return {"company": company.name if company else "?", "fiscal_year": filing.fiscal_year,
            "version": version}


@router.get("/checklist", response_model=list[schemas.ChecklistItem])
def checklist(filing_id: int, db: Session = Depends(get_db),
              user: models.User = Depends(get_current_user)):
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user)
    return pipeline.build_checklist(db, filing)


@router.get("/exports/checklist.pdf")
def checklist_pdf(filing_id: int, db: Session = Depends(get_db),
                  user: models.User = Depends(get_current_user)):
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user)
    items = pipeline.build_checklist(db, filing)
    pdf = exports.checklist_pdf(items, _meta(db, filing, ""))
    return Response(pdf, media_type=MEDIA["pdf"], headers={
        "Content-Disposition": f'attachment; filename="checklist-fy{filing.fiscal_year}.pdf"'})


@router.get("/exports/{filename}")
def export_statement(filing_id: int, filename: str, db: Session = Depends(get_db),
                     user: models.User = Depends(get_current_user)):
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user)
    if "." not in filename:
        raise HTTPException(400, "Expected <kind>.<fmt>, e.g. pl.pdf or bs.xlsx")
    kind, fmt = filename.rsplit(".", 1)
    if kind not in ("pl", "bs") or fmt not in MEDIA:
        raise HTTPException(400, "kind must be pl|bs and fmt must be pdf|xlsx")
    stmt = pipeline.latest_statement(db, filing_id, kind)
    if stmt is None:
        raise HTTPException(404, f"No {kind} statement generated yet")
    meta = _meta(db, filing, stmt.version)
    content = (exports.statement_pdf(kind, stmt.data, meta) if fmt == "pdf"
               else exports.statement_xlsx(kind, stmt.data, meta))
    return Response(content, media_type=MEDIA[fmt], headers={
        "Content-Disposition": f'attachment; filename="{kind}-fy{filing.fiscal_year}-v{stmt.version}.{fmt}"'})
