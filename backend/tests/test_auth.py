"""Auth/authorization tests: register/login/me, JWT validation, workspace ownership
guards, auth-aware tenant scoping, strict-mode enforcement, LLM rate limiting, CORS."""
import pytest
from fastapi.testclient import TestClient

import config
import server
from services import llm
from services.ratelimit import llm_limiter

LISTING_RESPONSE = {
    "listing_title": "Test title",
    "listing_description": "A great listing.",
    "suggested_price": 99.0,
    "hashtags": ["test"],
}


@pytest.fixture(scope="module")
def client():
    with TestClient(server.app) as c:
        yield c


@pytest.fixture(autouse=True)
def fake_llm(monkeypatch):
    async def fake_call_llm(system_message, prompt, image_b64=None):
        return dict(LISTING_RESPONSE)

    monkeypatch.setattr(llm, "call_llm", fake_call_llm)


def register(client, email, password="password123", name=None):
    r = client.post("/api/auth/register", json={"email": email, "password": password, "name": name, "accepted_terms": True})
    assert r.status_code == 200, r.text
    return r.json()


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_register_returns_token_and_clean_user(client):
    data = register(client, "owner@example.com")
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["email"] == "owner@example.com"
    assert "password_hash" not in data["user"]
    assert data["user"]["created_at"]


def test_register_creates_owned_default_workspace_with_connectors(client):
    data = register(client, "ownws@example.com")
    ws = client.get("/api/workspaces", headers=auth(data["access_token"])).json()
    mine = [w for w in ws if w.get("owner_id") == data["user"]["id"]]
    assert len(mine) >= 1
    assert any(w["is_default"] for w in mine)
    conns = client.get("/api/integrations", headers={**auth(data["access_token"]), "X-Workspace-Id": mine[0]["id"]}).json()
    assert len(conns) == 9


def test_duplicate_email_rejected(client):
    register(client, "dup@example.com")
    r = client.post("/api/auth/register", json={"email": "dup@example.com", "password": "password123", "accepted_terms": True})
    assert r.status_code == 400


def test_short_password_rejected(client):
    r = client.post("/api/auth/register", json={"email": "short@example.com", "password": "short"})
    assert r.status_code == 422


def test_register_requires_consent(client):
    # No consent checkbox -> account cannot be created (400 from the auth route).
    r = client.post("/api/auth/register", json={"email": "noconsent@example.com", "password": "password123"})
    assert r.status_code == 400
    r = client.post("/api/auth/register", json={"email": "noconsent@example.com", "password": "password123", "accepted_terms": False})
    assert r.status_code == 400
    # Consent given -> account created and consent record stored.
    data = register(client, "consent@example.com")
    me = client.get("/api/auth/me", headers=auth(data["access_token"])).json()
    assert me["accepted_terms"] is True
    assert me["accepted_terms_at"]
    assert me["accepted_terms_version"]


def test_login_success_and_wrong_password(client):
    register(client, "login@example.com")
    ok = client.post("/api/auth/login", json={"email": "login@example.com", "password": "password123"})
    assert ok.status_code == 200
    assert ok.json()["access_token"]
    bad = client.post("/api/auth/login", json={"email": "login@example.com", "password": "wrongpass1"})
    assert bad.status_code == 401


def test_me_requires_valid_token(client):
    register(client, "me@example.com")
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer bogus"}).status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Basic abc"}).status_code == 401
    r = client.get("/api/auth/me", headers=auth(client.post("/api/auth/login", json={"email": "me@example.com", "password": "password123"}).json()["access_token"]))
    assert r.status_code == 200
    assert r.json()["email"] == "me@example.com"


def test_workspace_ownership_guards(client):
    a = register(client, "owner-a@example.com")
    b = register(client, "owner-b@example.com")
    ws = client.post("/api/workspaces", headers=auth(a["access_token"]), json={"name": "A's Business"}).json()
    assert ws["owner_id"] == a["user"]["id"]
    assert client.get(f"/api/workspaces/{ws['id']}", headers=auth(b["access_token"])).status_code == 403
    assert client.put(f"/api/workspaces/{ws['id']}", headers=auth(b["access_token"]), json={"name": "hacked"}).status_code == 403
    assert client.get(f"/api/workspaces/{ws['id']}/export", headers=auth(b["access_token"])).status_code == 403
    assert client.get(f"/api/workspaces/{ws['id']}", headers=auth(a["access_token"])).status_code == 200
    b_ws = [w["id"] for w in client.get("/api/workspaces", headers=auth(b["access_token"])).json()]
    assert ws["id"] not in b_ws


def test_legacy_workspace_open_without_auth(client):
    ws = client.post("/api/workspaces", json={"name": "Legacy Open Business"}).json()
    assert ws.get("owner_id") is None
    assert client.get(f"/api/workspaces/{ws['id']}").status_code == 200


def test_tenant_validation_with_token(client):
    a = register(client, "tenant-a@example.com")
    b = register(client, "tenant-b@example.com")
    ws_a = [w for w in client.get("/api/workspaces", headers=auth(a["access_token"])).json() if w["is_default"]][0]
    ws_b = [w for w in client.get("/api/workspaces", headers=auth(b["access_token"])).json() if w["is_default"]][0]
    item = client.post("/api/items", headers={**auth(a["access_token"]), "X-Workspace-Id": ws_a["id"]},
                       json={"name": "A Item", "description": "d", "condition": "Good"}).json()
    # B presenting A's workspace header -> 403
    assert client.get(f"/api/items/{item['id']}", headers={**auth(b["access_token"]), "X-Workspace-Id": ws_a["id"]}).status_code == 403
    # No header -> each user falls back to their own default workspace (no leak)
    b_items = client.get("/api/items", headers=auth(b["access_token"])).json()
    assert all(i["workspace_id"] == ws_b["id"] for i in b_items)
    a_items = client.get("/api/items", headers=auth(a["access_token"])).json()
    assert all(i["workspace_id"] == ws_a["id"] for i in a_items)


def test_strict_mode_requires_auth_everywhere(client, monkeypatch):
    # ownerless legacy workspace created in grace mode (pre-existing data scenario)
    legacy = client.post("/api/workspaces", json={"name": "Legacy Strict"}).json()
    monkeypatch.setattr(config, "AUTH_REQUIRED", True)
    assert client.get("/api/items").status_code == 401
    assert client.get("/api/workspaces").status_code == 401
    assert client.post("/api/items", json={"name": "x", "description": "d", "condition": "Good"}).status_code == 401
    assert client.get("/api/auth/me").status_code == 401
    data = register(client, "strict@example.com")
    assert client.get("/api/auth/me", headers=auth(data["access_token"])).status_code == 200
    assert client.post("/api/auth/login", json={"email": "strict@example.com", "password": "password123"}).status_code == 200
    # ownerless legacy workspace is blocked for authenticated users in strict mode
    assert client.get(f"/api/workspaces/{legacy['id']}", headers=auth(data["access_token"])).status_code == 403


def test_rate_limit_on_llm_endpoints(client, monkeypatch):
    monkeypatch.setattr(llm_limiter, "max_calls", 2)
    ws_id = client.get("/api/workspaces").json()[0]["id"]
    h = {"X-Workspace-Id": ws_id}
    assert client.post("/api/ai/generate", headers=h, json={"name": "R1", "description": "d", "condition": "Good"}).status_code == 200
    assert client.post("/api/ai/generate", headers=h, json={"name": "R2", "description": "d", "condition": "Good"}).status_code == 200
    assert client.post("/api/ai/generate", headers=h, json={"name": "R3", "description": "d", "condition": "Good"}).status_code == 429
    llm_limiter.clear()


def test_cors_headers(client):
    r = client.options("/api/items", headers={"Origin": "http://example.com", "Access-Control-Request-Method": "GET"})
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin")
