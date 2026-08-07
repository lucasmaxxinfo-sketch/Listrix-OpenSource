"""TradeMe connector tests: staged legacy behavior, OAuth 1.0a flow, encrypted tokens
at rest, and approval-gated sync (suggestions only, never listing mutations)."""
import asyncio

import pytest
from fastapi.testclient import TestClient

import config
import server
from deps import db
from services.integrations import get_adapter

CONSUMER_KEY = "test-consumer-key"
CONSUMER_SECRET = "test-consumer-secret"
# valid 32-byte Fernet key (urlsafe-base64)
ENCRYPTION_KEY = "imyxa9xOJ1pCmSTezmMVwTnrJSzkTvxZozAKZN7i-4I="


@pytest.fixture(scope="module")
def client():
    with TestClient(server.app) as c:
        yield c


@pytest.fixture(autouse=True)
def fake_llm(monkeypatch):
    # generate_listing_ai is used to create listings for sync tests
    async def fake_call_llm(system_message, prompt, image_b64=None):
        return {"listing_title": "T", "listing_description": "D", "suggested_price": 200.0, "hashtags": ["test"]}

    from services import llm

    monkeypatch.setattr(llm, "call_llm", fake_call_llm)


def headers(wid):
    return {"X-Workspace-Id": wid}


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def make_workspace(client, name="Int Biz"):
    r = client.post("/api/workspaces", json={"name": name})
    assert r.status_code == 200
    return r.json()["id"]


def seed_connector_docs(client, wid):
    client.get("/api/integrations", headers=headers(wid))
    return run(db.integrations.find({"workspace_id": wid}, {"_id": 0}).to_list(50))


def test_connectors_seeded_and_tokens_never_exposed(client):
    wid = make_workspace(client)
    conns = client.get("/api/integrations", headers=headers(wid)).json()
    assert {c["platform"] for c in conns} == {"Stocksix", "TradeMe", "Facebook Marketplace", "Gmail", "Pricing Signals", "Competitor Listings"}
    assert all("tokens" not in c and "config" not in c for c in conns)


def test_legacy_simulated_connect_sync_preserved(client):
    """Without TRADEME consumer credentials the legacy toggle behavior must remain intact."""
    wid = make_workspace(client)
    connected = client.post("/api/integrations/TradeMe/connect", headers=headers(wid)).json()
    assert connected["auth_status"] == "connected"
    synced = client.post("/api/integrations/TradeMe/sync", headers=headers(wid)).json()
    assert synced["simulated"] is True
    assert "structure-only" in synced["note"].lower()
    assert client.post("/api/integrations/TradeMe/oauth/callback",
                       headers=headers(wid), json={"oauth_token": "t", "oauth_verifier": "v"}).status_code == 404
    disconnected = client.post("/api/integrations/TradeMe/connect", headers=headers(wid)).json()
    assert disconnected["auth_status"] == "disconnected"
    assert client.post("/api/integrations/TradeMe/sync", headers=headers(wid)).status_code == 400


@pytest.fixture
def trademe_configured(monkeypatch):
    monkeypatch.setattr(config, "TRADEME_CONSUMER_KEY", CONSUMER_KEY)
    monkeypatch.setattr(config, "TRADEME_CONSUMER_SECRET", CONSUMER_SECRET)
    monkeypatch.setattr(config, "CONNECTOR_ENCRYPTION_KEY", ENCRYPTION_KEY)
    return get_adapter("TradeMe")


def test_trademe_oauth_connect_callback_and_encryption(client, trademe_configured, monkeypatch):
    wid = make_workspace(client)
    adapter = trademe_configured

    async def fake_request_token(creds=None):
        return ("req-token", "req-secret")

    async def fake_access_token(creds, oauth_token, oauth_token_secret, oauth_verifier):
        return ("access-token", "access-secret")

    monkeypatch.setattr(adapter, "_fetch_request_token_pair", fake_request_token)
    monkeypatch.setattr(adapter, "_fetch_access_token_pair", fake_access_token)

    # connect -> authorization_required + authorize URL
    r = client.post("/api/integrations/TradeMe/connect", headers=headers(wid))
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "authorization_required"
    assert body["authorize_url"] == "https://api.trademe.co.nz/v1/OAuth/Authorize?oauth_token=req-token"
    assert body["auth_status"] == "authorizing"

    # stored OAuth state must be encrypted at rest
    doc = run(db.integrations.find_one({"platform": "TradeMe", "workspace_id": wid}, {"_id": 0}))
    assert doc["auth_status"] == "authorizing"
    assert "req-secret" not in doc["config"]
    assert "req-token" not in doc["config"]

    # mismatched token -> 400
    bad = client.post("/api/integrations/TradeMe/oauth/callback", headers=headers(wid),
                      json={"oauth_token": "wrong", "oauth_verifier": "v"})
    assert bad.status_code == 400

    # correct verifier -> connected, tokens encrypted at rest
    ok = client.post("/api/integrations/TradeMe/oauth/callback", headers=headers(wid),
                     json={"oauth_token": "req-token", "oauth_verifier": "123456"})
    assert ok.status_code == 200
    assert ok.json()["auth_status"] == "connected"
    doc = run(db.integrations.find_one({"platform": "TradeMe", "workspace_id": wid}, {"_id": 0}))
    assert "access-secret" not in doc["tokens"]
    assert "access-token" not in doc["tokens"]
    # sync_enabled flips on only after the callback completes
    assert doc["sync_enabled"] is True

    # tokens/config never exposed via the list endpoint
    exposed = [c for c in client.get("/api/integrations", headers=headers(wid)).json() if c["platform"] == "TradeMe"][0]
    assert "tokens" not in exposed and "config" not in exposed


def test_trademe_sync_creates_pending_suggestions_without_mutation(client, trademe_configured, monkeypatch):
    wid = make_workspace(client)
    adapter = trademe_configured
    item = client.post("/api/items", headers=headers(wid),
                       json={"name": "Trademe Item", "description": "d", "condition": "Good", "cost": 80.0}).json()
    listing = client.post("/api/ai/generate", headers=headers(wid),
                          json={"name": item["name"], "description": item["description"], "condition": item["condition"], "cost": 80.0, "item_id": item["id"]}).json()

    # complete OAuth quickly
    async def fake_request_token(creds=None):
        return ("req-token", "req-secret")

    async def fake_access_token(creds, oauth_token, oauth_token_secret, oauth_verifier):
        return ("access-token", "access-secret")

    monkeypatch.setattr(adapter, "_fetch_request_token_pair", fake_request_token)
    monkeypatch.setattr(adapter, "_fetch_access_token_pair", fake_access_token)
    client.post("/api/integrations/TradeMe/connect", headers=headers(wid))
    client.post("/api/integrations/TradeMe/oauth/callback", headers=headers(wid),
                json={"oauth_token": "req-token", "oauth_verifier": "123456"})

    # TradeMe has the item listed at $120; no local search fallback needed
    async def fake_selling(session):
        return [{"Title": "Trademe Item", "StartPrice": 120.0}]

    async def fake_search(session, query):
        return None

    monkeypatch.setattr(adapter, "_fetch_selling_listings", fake_selling)
    monkeypatch.setattr(adapter, "_search_median_price", fake_search)

    synced = client.post("/api/integrations/TradeMe/sync", headers=headers(wid))
    assert synced.status_code == 200, synced.text
    body = synced.json()
    assert body["simulated"] is False
    assert body["suggestions_created"] == 1

    # one pending reduce_price suggestion with the TradeMe anchor
    suggestions = client.get("/api/suggestions", headers=headers(wid)).json()
    assert len(suggestions) == 1
    s = suggestions[0]
    assert s["type"] == "reduce_price"
    assert s["status"] == "pending"
    assert s["params"]["new_price"] == 120.0

    # approval gate: the listing itself was NOT changed
    after = client.get("/api/listings", headers=headers(wid)).json()[0]
    assert after["suggested_price"] == listing["suggested_price"]

    # idempotent re-sync keeps exactly one pending suggestion (re-queued with a fresh id)
    client.post("/api/integrations/TradeMe/sync", headers=headers(wid))
    suggestions = client.get("/api/suggestions", headers=headers(wid)).json()
    assert len(suggestions) == 1
    s = suggestions[0]

    # approval flow works on the queued suggestion (control layer)
    applied = client.post(f"/api/suggestions/{s['id']}/apply", headers=headers(wid))
    assert applied.status_code == 200
    assert client.get("/api/listings", headers=headers(wid)).json()[0]["suggested_price"] == 120.0


def test_trademe_sync_uses_search_when_no_exact_match(client, trademe_configured, monkeypatch):
    wid = make_workspace(client)
    adapter = trademe_configured
    item = client.post("/api/items", headers=headers(wid),
                       json={"name": "No Match Item", "description": "d", "condition": "Good", "cost": 60.0}).json()
    client.post("/api/ai/generate", headers=headers(wid),
                json={"name": item["name"], "description": item["description"], "condition": item["condition"], "cost": 60.0, "item_id": item["id"]})

    async def fake_request_token(creds=None):
        return ("req-token", "req-secret")

    async def fake_access_token(creds, oauth_token, oauth_token_secret, oauth_verifier):
        return ("access-token", "access-secret")

    monkeypatch.setattr(adapter, "_fetch_request_token_pair", fake_request_token)
    monkeypatch.setattr(adapter, "_fetch_access_token_pair", fake_access_token)
    client.post("/api/integrations/TradeMe/connect", headers=headers(wid))
    client.post("/api/integrations/TradeMe/oauth/callback", headers=headers(wid),
                json={"oauth_token": "req-token", "oauth_verifier": "123456"})

    async def fake_selling(session):
        return [{"Title": "Something Else", "StartPrice": 500.0}]

    async def fake_search(session, query):
        assert query == "No Match Item"
        return 140.0

    monkeypatch.setattr(adapter, "_fetch_selling_listings", fake_selling)
    monkeypatch.setattr(adapter, "_search_median_price", fake_search)

    body = client.post("/api/integrations/TradeMe/sync", headers=headers(wid)).json()
    assert body["suggestions_created"] == 1
    assert client.get("/api/suggestions", headers=headers(wid)).json()[0]["params"]["new_price"] == 140.0


def test_trademe_sync_skips_when_anchor_is_not_below_threshold(client, trademe_configured, monkeypatch):
    wid = make_workspace(client)
    adapter = trademe_configured
    item = client.post("/api/items", headers=headers(wid),
                       json={"name": "Fair Priced Item", "description": "d", "condition": "Good", "cost": 100.0}).json()
    client.post("/api/ai/generate", headers=headers(wid),
                json={"name": item["name"], "description": item["description"], "condition": item["condition"], "cost": 100.0, "item_id": item["id"]})

    async def fake_request_token(creds=None):
        return ("req-token", "req-secret")

    async def fake_access_token(creds, oauth_token, oauth_token_secret, oauth_verifier):
        return ("access-token", "access-secret")

    monkeypatch.setattr(adapter, "_fetch_request_token_pair", fake_request_token)
    monkeypatch.setattr(adapter, "_fetch_access_token_pair", fake_access_token)
    client.post("/api/integrations/TradeMe/connect", headers=headers(wid))
    client.post("/api/integrations/TradeMe/oauth/callback", headers=headers(wid),
                json={"oauth_token": "req-token", "oauth_verifier": "123456"})

    async def fake_selling(session):
        return [{"Title": "Fair Priced Item", "StartPrice": 195.0}]  # >= 95% of 200 -> no suggestion

    monkeypatch.setattr(adapter, "_fetch_selling_listings", fake_selling)

    body = client.post("/api/integrations/TradeMe/sync", headers=headers(wid)).json()
    assert body["suggestions_created"] == 0
    assert client.get("/api/suggestions", headers=headers(wid)).json() == []


# ---- Facebook Marketplace adapter (staged real) ---------------------------------
FB_TOKEN = "fb-test-page-token"


@pytest.fixture
def facebook_configured(monkeypatch):
    monkeypatch.setattr(config, "FACEBOOK_PAGE_TOKEN", FB_TOKEN)
    monkeypatch.setattr(config, "CONNECTOR_ENCRYPTION_KEY", ENCRYPTION_KEY)


def test_facebook_connect_and_sync_queues_pending_suggestion(client, facebook_configured, monkeypatch):
    from services.integrations import get_adapter as ga

    adapter = ga("Facebook Marketplace")
    wid = make_workspace(client)
    item = client.post("/api/items", headers=headers(wid), json={
        "name": "Sony Headphones", "description": "Wireless", "condition": "Like New", "cost": 100.0}).json()
    client.post("/api/ai/generate", headers=headers(wid), json={
        "name": "Sony Headphones", "description": "Wireless", "condition": "Like New",
        "cost": 100.0, "item_id": item["id"]})  # listing price 200.0 (fake LLM)

    monkeypatch.setattr(adapter, "_fetch_listings", lambda creds: [{"name": "Sony Headphones", "price": "149.00"}])
    r = client.post("/api/integrations/Facebook Marketplace/connect", headers=headers(wid))
    assert r.status_code == 200, r.text
    assert r.json()["auth_status"] == "connected"

    r = client.post("/api/integrations/Facebook Marketplace/sync", headers=headers(wid))
    assert r.status_code == 200, r.text
    assert r.json()["suggestions_queued"] == 1

    pending = client.get("/api/suggestions", headers=headers(wid)).json()
    sug = [s for s in pending if s["type"] == "reduce_price" and s["params"].get("source") == "facebook"]
    assert len(sug) == 1
    assert sug[0]["params"]["new_price"] == 149.0
    assert sug[0]["status"] == "pending"

    # approval-gated: the listing itself is untouched
    listing = client.get("/api/listings", headers=headers(wid)).json()[0]
    assert listing["suggested_price"] == 200.0

    # tokens never leak from the list endpoint
    conns = client.get("/api/integrations", headers=headers(wid)).json()
    assert all("tokens" not in c for c in conns)


def test_facebook_sync_skips_anchor_near_current_price(client, facebook_configured, monkeypatch):
    from services.integrations import get_adapter as ga

    adapter = ga("Facebook Marketplace")
    wid = make_workspace(client)
    item = client.post("/api/items", headers=headers(wid), json={
        "name": "Chair", "description": "Wooden", "condition": "Good", "cost": 50.0}).json()
    client.post("/api/ai/generate", headers=headers(wid), json={
        "name": "Chair", "description": "Wooden", "condition": "Good", "cost": 50.0, "item_id": item["id"]})
    monkeypatch.setattr(adapter, "_fetch_listings", lambda creds: [{"name": "Chair", "price": "195.00"}])  # 200*0.95
    client.post("/api/integrations/Facebook Marketplace/connect", headers=headers(wid))
    r = client.post("/api/integrations/Facebook Marketplace/sync", headers=headers(wid)).json()
    assert r["suggestions_queued"] == 0


def test_unconfigured_facebook_keeps_legacy_toggle(client):
    wid = make_workspace(client)
    r = client.post("/api/integrations/Facebook Marketplace/connect", headers=headers(wid))
    assert r.status_code == 200, r.text
    assert r.json()["auth_status"] == "connected"  # legacy simulated toggle
    r = client.post("/api/integrations/Facebook Marketplace/sync", headers=headers(wid))
    assert r.status_code == 200 and r.json().get("simulated") is True


# ---- Gmail adapter (staged real) --------------------------------------------------
GMAIL_TOKEN = "gmail-test-access-token"


@pytest.fixture
def gmail_configured(monkeypatch):
    monkeypatch.setattr(config, "GMAIL_ACCESS_TOKEN", GMAIL_TOKEN)
    monkeypatch.setattr(config, "CONNECTOR_ENCRYPTION_KEY", ENCRYPTION_KEY)


def test_gmail_connect_sync_imports_buyer_messages(client, gmail_configured, monkeypatch):
    from services.integrations import get_adapter as ga

    adapter = ga("Gmail")
    wid = make_workspace(client)
    client.post("/api/items", headers=headers(wid), json={
        "name": "Sony Headphones", "description": "Wireless", "condition": "Good", "cost": 100.0})

    monkeypatch.setattr(adapter, "_fetch_message_ids", lambda creds: ["msg-1"])
    monkeypatch.setattr(adapter, "_fetch_message", lambda creds, mid: {
        "id": mid,
        "payload": {"headers": [{"name": "From", "value": "buyer@example.com"},
                                {"name": "Subject", "value": "Question about Sony Headphones"}]},
        "snippet": "Is this still available? Would you accept $150?",
    })

    r = client.post("/api/integrations/Gmail/connect", headers=headers(wid))
    assert r.status_code == 200 and r.json()["auth_status"] == "connected"

    r = client.post("/api/integrations/Gmail/sync", headers=headers(wid))
    assert r.status_code == 200, r.text
    assert r.json()["messages_imported"] == 1

    inbox = client.get("/api/inbox", headers=headers(wid)).json()
    gmails = [m for m in inbox if m.get("source") == "gmail"]
    assert len(gmails) == 1
    assert gmails[0]["simulated"] is False
    assert gmails[0]["related_item_name"] == "Sony Headphones"
    assert gmails[0]["read"] is False

    # replies on real messages become drafts (no auto-send)
    r = client.post(f"/api/inbox/{gmails[0]['id']}/reply", headers=headers(wid), json={"text": "Yes, still available."})
    assert r.status_code == 200 and r.json()["reply_draft"]


def test_gmail_refresh_merges_real_messages_when_connected(client, gmail_configured, monkeypatch):
    from services.integrations import get_adapter as ga

    adapter = ga("Gmail")
    wid = make_workspace(client)
    client.post("/api/items", headers=headers(wid), json={
        "name": "Lamp", "description": "Desk lamp", "condition": "Good", "cost": 20.0})
    monkeypatch.setattr(adapter, "_fetch_message_ids", lambda creds: ["m2"])
    monkeypatch.setattr(adapter, "_fetch_message", lambda creds, mid: {
        "id": mid, "payload": {"headers": [{"name": "From", "value": "a@b.com"},
                                           {"name": "Subject", "value": "Lamp question"}]}, "snippet": "Hi"})
    client.post("/api/integrations/Gmail/connect", headers=headers(wid))
    r = client.post("/api/inbox/refresh", headers=headers(wid)).json()
    assert r["gmail_imported"] == 1
    assert any(m.get("source") == "gmail" for m in client.get("/api/inbox", headers=headers(wid)).json())


# ---- multi-user roles / members (staged) -------------------------------------------
def test_member_invite_roles_and_owner_guard(client):
    owner = client.post("/api/auth/register", json={"email": "ws-owner@example.com", "password": "password123", "name": "Owner"}).json()
    member = client.post("/api/auth/register", json={"email": "ws-member@example.com", "password": "password123", "name": "Member"}).json()
    oa = {"Authorization": f"Bearer {owner['access_token']}"}
    ma = {"Authorization": f"Bearer {member['access_token']}"}

    wid = client.post("/api/workspaces", headers=oa, json={"name": "Shared WS"}).json()["id"]

    # owner invites member
    r = client.post(f"/api/workspaces/{wid}/members", headers=oa, json={"email": "ws-member@example.com", "role": "member"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "active"

    # member can list members but not update workspace settings
    assert client.get(f"/api/workspaces/{wid}/members", headers=ma).status_code == 200
    assert client.put(f"/api/workspaces/{wid}", headers=ma, json={"primary_color": "#000000"}).status_code == 403
    assert client.post(f"/api/workspaces/{wid}/members", headers=ma, json={"email": "x@y.com"}).status_code == 403

    # non-member third user cannot even view members
    third = client.post("/api/auth/register", json={"email": "ws-third@example.com", "password": "password123"}).json()
    assert client.get(f"/api/workspaces/{wid}/members", headers={"Authorization": f"Bearer {third['access_token']}"}).status_code == 403

    # owner removes member
    members = client.get(f"/api/workspaces/{wid}/members", headers=oa).json()
    member_id = members[0]["id"]
    assert client.delete(f"/api/workspaces/{wid}/members/{member_id}", headers=oa).status_code == 200
    assert client.get(f"/api/workspaces/{wid}/members", headers=oa).json() == []


# ---- Connection Wizard (in-app live credentials) -----------------------------------
def test_wizard_config_saved_encrypted_and_never_exposed(client):
    wid = make_workspace(client)
    saved = client.post("/api/integrations/Gmail/config", headers=headers(wid),
                        json={"credentials": {"access_token": "wizard-gmail-token"}})
    assert saved.status_code == 200, saved.text
    assert saved.json()["configured"] is True

    # encrypted at rest, plaintext never stored
    doc = run(db.integrations.find_one({"platform": "Gmail", "workspace_id": wid}, {"_id": 0}))
    assert doc["auth_status"] == "configured"
    assert "wizard-gmail-token" not in doc["setup"]
    assert "wizard-gmail-token" not in str(doc)

    # never exposed via list or status
    listed = client.get("/api/integrations", headers=headers(wid)).json()
    g = next(c for c in listed if c["platform"] == "Gmail")
    assert all(k not in g for k in ("tokens", "config", "setup"))
    status = client.get("/api/integrations/status", headers=headers(wid)).json()
    s = next(c for c in status if c["platform"] == "Gmail")
    assert s["mode"] == "live" and s["configured"] is True and s["credentials_stored"] is True
    assert "wizard-gmail-token" not in str(status)


def test_wizard_test_endpoint_and_last_test_recorded(client, monkeypatch):
    from services.integrations import get_adapter as ga

    adapter = ga("Gmail")
    wid = make_workspace(client)
    client.post("/api/integrations/Gmail/config", headers=headers(wid),
                json={"credentials": {"access_token": "tok"}})

    async def fake_test(wid):
        return {"ok": True, "message": "Gmail accepted your access token."}

    monkeypatch.setattr(adapter, "test", fake_test)
    r = client.post("/api/integrations/Gmail/test", headers=headers(wid))
    assert r.status_code == 200 and r.json()["ok"] is True
    assert "at" in r.json()
    doc = run(db.integrations.find_one({"platform": "Gmail", "workspace_id": wid}, {"_id": 0}))
    assert doc["last_test"]["ok"] is True

    # failure path stores the failure too
    async def fake_test_fail(wid):
        return {"ok": False, "message": "bad token"}

    monkeypatch.setattr(adapter, "test", fake_test_fail)
    r = client.post("/api/integrations/Gmail/test", headers=headers(wid))
    assert r.json()["ok"] is False
    status = client.get("/api/integrations/status", headers=headers(wid)).json()
    assert next(c for c in status if c["platform"] == "Gmail")["last_test"]["ok"] is False


def test_wizard_stored_creds_drive_live_trademe_flow_without_env(client, monkeypatch):
    """Wizard-saved consumer creds must enable the real OAuth flow even with no env vars."""
    from services.integrations import get_adapter as ga

    adapter = ga("TradeMe")
    wid = make_workspace(client)
    client.post("/api/integrations/TradeMe/config", headers=headers(wid), json={
        "credentials": {"consumer_key": "wizard-key", "consumer_secret": "wizard-secret", "callback_url": "https://app.example/cb"}})

    async def fake_request_token(creds=None):
        assert creds["consumer_key"] == "wizard-key"
        assert creds["consumer_secret"] == "wizard-secret"
        return ("wiz-req-token", "wiz-req-secret")

    monkeypatch.setattr(adapter, "_fetch_request_token_pair", fake_request_token)
    r = client.post("/api/integrations/TradeMe/connect", headers=headers(wid))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "authorization_required"
    assert "wiz-req-token" in body["authorize_url"]
    assert "callback=https%3A%2F%2Fapp.example%2Fcb" in body["authorize_url"] or "app.example" in body["authorize_url"]

    # callback now accepted (guard checks stored creds, not env)
    async def fake_access(creds, oauth_token, oauth_token_secret, oauth_verifier):
        return ("wiz-access", "wiz-access-secret")

    monkeypatch.setattr(adapter, "_fetch_access_token_pair", fake_access)
    r = client.post("/api/integrations/TradeMe/oauth/callback", headers=headers(wid),
                    json={"oauth_token": "wiz-req-token", "oauth_verifier": "123456"})
    assert r.status_code == 200 and r.json()["auth_status"] == "connected"


def test_wizard_disconnect_clears_credentials_and_blocks_sync(client):
    wid = make_workspace(client)
    client.post("/api/integrations/Gmail/config", headers=headers(wid),
                json={"credentials": {"access_token": "tok"}})
    r = client.post("/api/integrations/Gmail/disconnect", headers=headers(wid))
    assert r.status_code == 200 and r.json()["auth_status"] == "disconnected"
    doc = run(db.integrations.find_one({"platform": "Gmail", "workspace_id": wid}, {"_id": 0}))
    assert doc.get("setup") is None and doc.get("tokens") is None
    status = client.get("/api/integrations/status", headers=headers(wid)).json()
    s = next(c for c in status if c["platform"] == "Gmail")
    assert s["mode"] == "simulated" and s["credentials_stored"] is False
    assert client.post("/api/integrations/Gmail/sync", headers=headers(wid)).status_code == 400


def test_wizard_rejects_credentials_for_simulated_platforms(client):
    wid = make_workspace(client)
    assert client.post("/api/integrations/Pricing Signals/config", headers=headers(wid),
                       json={"credentials": {"anything": "x"}}).status_code == 404
    assert client.post("/api/integrations/Pricing Signals/test", headers=headers(wid)).status_code == 404
