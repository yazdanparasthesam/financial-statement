from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import get_current_user
from ..security import create_token, hash_password, verify_password
from ..services.audit import log_event

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserOut, status_code=201)
def register(body: schemas.UserCreate, db: Session = Depends(get_db)):
    if body.role not in ("preparer", "reviewer"):
        raise HTTPException(400, "role must be 'preparer' or 'reviewer'")
    if db.scalar(select(models.User).where(models.User.email == body.email)):
        raise HTTPException(409, "Email already registered")
    user = models.User(email=body.email, password_hash=hash_password(body.password),
                       full_name=body.full_name, role=body.role)
    db.add(user)
    db.flush()
    log_event(db, actor_id=user.id, action="auth.register", entity="user", entity_id=user.id,
              detail={"role": user.role})
    db.commit()
    return user


@router.post("/login", response_model=schemas.TokenOut)
def login(body: schemas.LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(models.User).where(models.User.email == body.email))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return schemas.TokenOut(access_token=create_token(user.id, user.email, user.role), user=user)


@router.get("/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    return user
