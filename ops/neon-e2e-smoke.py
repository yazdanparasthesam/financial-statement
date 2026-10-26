#!/usr/bin/env python3
"""Safe end-to-end smoke for the app against the currently checked-out Neon branch.

Run from the repository root with the backend dependencies installed:
    backend/.venv/bin/python ops/neon-e2e-smoke.py

The script reads ignored dotenv files without printing values, normalizes Neon’s
standard PostgreSQL URL for the project’s existing psycopg 3 driver, starts the
FastAPI ASGI app, performs a temporary register/login/me journey, and removes the
temporary user and its audit row. Run only while `neon-smoke` is checked out; do
not run against production.
"""
from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"


def load_dotenv_environment() -> None:
    """Load backend/.env, root .env, then root .env.local without printing values."""
    try:
        from dotenv import dotenv_values
    except ImportError as exc:  # pragma: no cover - depends on local installation
        raise RuntimeError("Install backend/requirements.txt before running this smoke") from exc

    values: dict[str, str | None] = {}
    for path in (BACKEND / ".env", ROOT / ".env", ROOT / ".env.local"):
        if path.is_file():
            values.update(dotenv_values(path))
    for key, value in values.items():
        if value is not None:
            os.environ.setdefault(key, value)

    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL is not available from the checked-out branch")
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    os.environ["DATABASE_URL"] = url
    os.environ["AI_PROVIDER"] = "mock"
    os.environ["OTEL_ENABLED"] = "false"
    # A one-process test key; it is neither printed nor written to any file.
    os.environ["JWT_SECRET"] = secrets.token_urlsafe(48)


def main() -> int:
    load_dotenv_environment()
    sys.path.insert(0, str(BACKEND))

    from app.db import SessionLocal
    from app.main import app
    from app.models import AuditLog, User
    from fastapi.testclient import TestClient
    from sqlalchemy import delete, select
    from sqlalchemy.exc import SQLAlchemyError

    email = f"neon-smoke-{uuid4().hex}@example.com"
    statuses: dict[str, int] = {}
    cleanup_ok = True

    try:
        with TestClient(app) as client:
            health = client.get("/healthz")
            statuses["healthz"] = health.status_code
            if health.status_code != 200:
                raise RuntimeError("/healthz did not return HTTP 200")

            created = client.post("/api/auth/register", json={
                "email": email,
                "password": "Neon-Smoke-Only-Password-48!",
                "full_name": "Neon integration smoke",
                "role": "preparer",
            })
            statuses["register"] = created.status_code
            if created.status_code != 201:
                raise RuntimeError("temporary registration did not return HTTP 201")

            logged_in = client.post("/api/auth/login", json={
                "email": email,
                "password": "Neon-Smoke-Only-Password-48!",
            })
            statuses["login"] = logged_in.status_code
            if logged_in.status_code != 200:
                raise RuntimeError("temporary login did not return HTTP 200")

            token = logged_in.json()["access_token"]
            current_user = client.get("/api/auth/me", headers={
                "Authorization": f"Bearer {token}",
            })
            statuses["me"] = current_user.status_code
            if current_user.status_code != 200 or current_user.json().get("email") != email:
                raise RuntimeError("authenticated /me check failed")
    finally:
        # Remove only this run's synthetic user and the audit row created at registration.
        try:
            with SessionLocal() as db:
                user = db.scalar(select(User).where(User.email == email))
                if user is not None:
                    db.execute(delete(AuditLog).where(AuditLog.actor_id == user.id))
                    db.delete(user)
                    db.commit()
        except SQLAlchemyError:
            cleanup_ok = False

    if not cleanup_ok:
        raise RuntimeError("smoke passed partially but temporary test-user cleanup failed")
    print("PASS Neon app smoke: " + ", ".join(
        f"{name}={code}" for name, code in statuses.items()
    ) + "; temporary user cleaned up")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 - top-level CLI must sanitize all errors
        # Avoid dumping configuration, connection URLs, or tokens in terminal output.
        print(f"FAIL Neon app smoke: {type(exc).__name__}; inspect local traceback/config privately")
        raise SystemExit(1)
