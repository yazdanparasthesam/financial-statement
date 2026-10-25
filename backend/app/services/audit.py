"""Audit-trail writer: every state-changing action gets a row (criterion: workflow trust)."""
from sqlalchemy.orm import Session

from .. import models


def log_event(db: Session, *, actor_id: int | None, action: str, entity: str,
              entity_id: int | None = None, detail: dict | None = None) -> None:
    db.add(models.AuditLog(actor_id=actor_id, action=action, entity=entity,
                           entity_id=entity_id, detail=detail))
