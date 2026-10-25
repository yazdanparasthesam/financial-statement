import pytest

from tests.conftest import PASSWORD, register_and_login


@pytest.mark.integration
def test_register_login_me(client):
    headers = register_and_login(client)
    me = client.get("/api/auth/me", headers=headers).json()
    assert me["role"] == "preparer" and me["email"].endswith("@example.com")
    assert "password" not in me and "password_hash" not in me


@pytest.mark.integration
def test_duplicate_email_409(client):
    import uuid
    email = f"dup-{uuid.uuid4().hex[:8]}@example.com"
    body = {"email": email, "password": PASSWORD, "role": "preparer"}
    assert client.post("/api/auth/register", json=body).status_code == 201
    assert client.post("/api/auth/register", json=body).status_code == 409


@pytest.mark.integration
def test_validation_and_bad_credentials(client):
    assert client.post("/api/auth/register", json={
        "email": "short@example.com", "password": "123", "role": "preparer"}).status_code == 422
    assert client.post("/api/auth/register", json={
        "email": "role@example.com", "password": PASSWORD, "role": "wizard"}).status_code == 400
    register_and_login(client)
    assert client.post("/api/auth/login", json={
        "email": "nobody@example.com", "password": PASSWORD}).status_code == 401


@pytest.mark.integration
def test_protected_endpoint_requires_token(client):
    assert client.get("/api/companies").status_code in (401, 403)
    assert client.get("/api/companies", headers={"Authorization": "Bearer garbage"}).status_code == 401


@pytest.mark.integration
def test_healthz_and_version(client):
    assert client.get("/healthz").json() == {"status": "ok"}
    v = client.get("/version").json()
    assert v["app"] == "Financial Statement" and v["ai_provider"] == "mock"
