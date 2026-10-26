"""Test bootstrap: env is configured BEFORE the app imports (lru_cached settings).

Unit tests (tests/unit) are pure — no DB, no HTTP.
Integration tests (tests/integration) drive the real app + database via TestClient.
"""
import os
import pathlib
import tempfile
from uuid import uuid4

_tmp = pathlib.Path(tempfile.mkdtemp(prefix="fs-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp / 'test.db'}"
os.environ["AI_PROVIDER"] = "mock"
os.environ["JWT_SECRET"] = "test-secret-not-for-prod-use-32-byte-minimum-key"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SEED_DIR = REPO_ROOT / "seed"
PASSWORD = "test-password-123"


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.create_all(engine)
    yield


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def register_and_login(client, role="preparer"):
    email = f"{role}-{uuid4().hex[:10]}@example.com"
    r = client.post("/api/auth/register", json={
        "email": email, "password": PASSWORD, "full_name": role.title(), "role": role})
    assert r.status_code == 201, r.text
    r = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def preparer(client):
    return register_and_login(client, "preparer")


@pytest.fixture()
def reviewer(client):
    return register_and_login(client, "reviewer")


@pytest.fixture()
def company(client, preparer):
    r = client.post("/api/companies", headers=preparer, json={
        "name": "Test Co", "national_id": "T-1", "economic_code": "E-1",
        "fiscal_year_end_month": 3})
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture()
def filing(client, preparer, company):
    r = client.post("/api/filings", headers=preparer,
                    json={"company_id": company["id"], "fiscal_year": 2025})
    assert r.status_code == 201, r.text
    return r.json()


def seed_bytes(name: str) -> bytes:
    return (SEED_DIR / name).read_bytes()


def upload_tb(client, headers, filing_id, name):
    r = client.post(f"/api/filings/{filing_id}/trial-balance", headers=headers,
                    files={"file": (name, seed_bytes(name), "text/csv")})
    assert r.status_code == 200, r.text
    return r.json()
