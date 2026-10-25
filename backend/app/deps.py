"""Shared FastAPI dependencies: DB session, current user, role guard, filing access."""
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from . import models
from .db import get_db
from .security import decode_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> models.User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = decode_token(creds.credentials)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token") from exc
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists")
    return user


def require_role(*roles: str):
    def guard(user: models.User = Depends(get_current_user)) -> models.User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Requires role: {'|'.join(roles)}")
        return user

    return guard


def get_filing_or_404(db: Session, filing_id: int) -> models.Filing:
    filing = db.get(models.Filing, filing_id)
    if filing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Filing not found")
    return filing


def ensure_access(db: Session, filing: models.Filing, user: models.User, write: bool = False) -> None:
    """Owner (preparer) has full access to own filings; reviewers get read access
    everywhere and write access only through review endpoints (checked separately)."""
    company = db.get(models.Company, filing.company_id)
    is_owner = company is not None and company.owner_id == user.id
    if is_owner:
        return
    if user.role == "reviewer" and not write:
        return
    raise HTTPException(status.HTTP_403_FORBIDDEN, "No access to this filing")
