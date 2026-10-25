import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import ensure_access, get_current_user, get_filing_or_404
from ..domain.workflow import allowed_actions, can_transition
from ..infra.telemetry import inc_transition, observe_journey_step
from ..services import pipeline
from ..services.audit import log_event

router = APIRouter(prefix="/api/filings/{filing_id}", tags=["workflow"])


def _gate_errors(db: Session, filing: models.Filing, action: str) -> str | None:
    """Deterministic submit/accept gates: no failing error-rules allowed."""
    if action not in ("submit", "accept"):
        return None
    run = db.scalar(select(models.ValidationRun).where(models.ValidationRun.filing_id == filing.id)
                    .order_by(models.ValidationRun.id.desc()))
    if run is None:
        return "Run validation before this action — no validation run on file."
    if run.failed > 0:
        failed = db.scalars(select(models.ValidationResult).where(
            models.ValidationResult.run_id == run.id, models.ValidationResult.passed == False,  # noqa: E712
            models.ValidationResult.severity == "error")).all()
        if failed:
            return "Resolve failing error-rules first: " + ", ".join(r.rule_id for r in failed)
    if action == "submit":
        has_pl = pipeline.latest_statement(db, filing.id, "pl") is not None
        if not has_pl:
            return "Generate statements before submitting."
    return None


def _transition(db: Session, filing: models.Filing, user: models.User,
                action: str, comment: str) -> models.Filing:
    t0 = time.monotonic()
    ok, result = can_transition(filing.status, action, user.role)
    if not ok:
        raise HTTPException(422, result)
    gate = _gate_errors(db, filing, action)
    if gate:
        raise HTTPException(422, gate)
    frm = filing.status
    filing.status = result
    db.add(models.ReviewEvent(filing_id=filing.id, actor_id=user.id,
                              from_status=frm, to_status=result, comment=comment))
    log_event(db, actor_id=user.id, action=f"workflow.{action}", entity="filing",
              entity_id=filing.id, detail={"from": frm, "to": result})
    db.commit()
    inc_transition(action, result)
    if action == "submit":
        observe_journey_step("submit", time.monotonic() - t0)
    return filing


@router.post("/submit", response_model=schemas.FilingOut)
def submit(filing_id: int, db: Session = Depends(get_db),
           user: models.User = Depends(get_current_user)):
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user, write=True)
    return _transition(db, filing, user, "submit", "")


@router.post("/review/transition", response_model=schemas.FilingOut)
def review_transition(filing_id: int, body: schemas.TransitionIn, db: Session = Depends(get_db),
                      user: models.User = Depends(get_current_user)):
    filing = get_filing_or_404(db, filing_id)
    if body.action in ("start_review", "request_changes", "accept", "reject"):
        if user.role != "reviewer":
            raise HTTPException(403, "Only reviewers can perform this action")
    else:
        ensure_access(db, filing, user, write=True)
    return _transition(db, filing, user, body.action, body.comment)


@router.get("/review/actions", response_model=list[str])
def review_actions(filing_id: int, db: Session = Depends(get_db),
                   user: models.User = Depends(get_current_user)):
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user)
    return allowed_actions(filing.status, user.role)


@router.get("/review/events", response_model=list[schemas.ReviewEventOut])
def review_events(filing_id: int, db: Session = Depends(get_db),
                  user: models.User = Depends(get_current_user)):
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user)
    return db.scalars(select(models.ReviewEvent).where(models.ReviewEvent.filing_id == filing_id)
                      .order_by(models.ReviewEvent.id)).all()


@router.post("/comments", response_model=schemas.CommentOut, status_code=201)
def add_comment(filing_id: int, body: schemas.CommentCreate, db: Session = Depends(get_db),
                user: models.User = Depends(get_current_user)):
    filing = get_filing_or_404(db, filing_id)
    if user.role != "reviewer":
        ensure_access(db, filing, user, write=True)
    comment = models.ReviewComment(filing_id=filing_id, author_id=user.id,
                                   anchor=body.anchor, body=body.body)
    db.add(comment)
    db.flush()
    log_event(db, actor_id=user.id, action="comment.add", entity="filing", entity_id=filing_id,
              detail={"anchor": body.anchor, "comment_id": comment.id})
    db.commit()
    return comment


@router.get("/comments", response_model=list[schemas.CommentOut])
def list_comments(filing_id: int, db: Session = Depends(get_db),
                  user: models.User = Depends(get_current_user)):
    filing = get_filing_or_404(db, filing_id)
    ensure_access(db, filing, user)
    return db.scalars(select(models.ReviewComment).where(models.ReviewComment.filing_id == filing_id)
                      .order_by(models.ReviewComment.id)).all()


@router.patch("/comments/{comment_id}/resolve", response_model=schemas.CommentOut)
def resolve_comment(filing_id: int, comment_id: int, db: Session = Depends(get_db),
                    user: models.User = Depends(get_current_user)):
    comment = db.get(models.ReviewComment, comment_id)
    if comment is None or comment.filing_id != filing_id:
        raise HTTPException(404, "Comment not found")
    comment.resolved = True
    log_event(db, actor_id=user.id, action="comment.resolve", entity="comment", entity_id=comment.id)
    db.commit()
    return comment
