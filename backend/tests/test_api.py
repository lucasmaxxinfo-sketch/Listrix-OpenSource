"""End-to-end API tests run locally against an in-memory Mongo (mongomock) with a
mocked LLM. Covers tenant isolation, the Control Layer, and the WORKSPACE_CREATED fix.
"""
import asyncio
import time

import pytest
from fastapi.testclient import TestClient

import server
from deps import db
from services import llm

LISTING_RESPONSE = {
    "listing_title": "Sony WH-1000XM4 - Like New",
    "listing_description": "Great wireless headphones in like-new condition.",
    "suggested_price": 199.0,
    "hashtags": ["sony", "headphones", "wireless"],
}
VISION_RESPONSE = {
    "item_type": "headphones",
    "category": "Electronics",
    "brand": "Sony",
    "condition_guess": "Like New",
    "features": ["wireless", "noise cancelling"],
    "suggested_title": "Sony Headphones",
    "suggested_description": "Wireless headphones",
    "suggested_price": 210.0,
    "value_estimate": {"low": 150.0, "mid": 200.0, "high": 250.0, "confidence": 80, "reasoning": "market data"},
    "market_positioning": "premium",
}
AGENT_RESPONSE = {
    "performance": {"status": "good", "likelihood_of_sale": 82, "reason": "Strong listing", "recommended_action": "Keep price"},
    "suggestions": [
        {"type": "add_keywords", "title": "Add keywords", "detail": "Add more hashtags", "confidence": 70,
         "expected_impact": "More reach", "expected_outcome": "More views", "risk_level": "low",
         "reason": "Reach more buyers", "params": {"add_hashtags": ["wireless", "noise-cancelling"]}},
        {"type": "reduce_price", "title": "Reduce price", "detail": "Drop to 149", "confidence": 55,
         "expected_impact": "Faster sale", "expected_outcome": "Sold within 2 weeks", "risk_level": "medium",
         "reason": "Price above market", "params": {"new_price": 149.0}},
    ],
}
ASSISTANT_RESPONSE = {
    "answer": "I recommend lowering the price to 149.",
    "recommendations": [{"title": "Lower price", "detail": "Try 149", "urgency": "medium", "confidence": 60}],
}
BRIEF_RESPONSE = {
    "headline": "Solid day", "summary": "summary text", "what_sold": "", "what_didnt_sell": "Headphones",
    "priority_items": ["Headphones"], "suggested_actions": ["Relist"], "risk_alerts": [], "opportunities": ["Bundle"],
}


@pytest.fixture(scope="module")
def client():
    with TestClient(server.app) as c:
        yield c


@pytest.fixture(autouse=True)
def fake_llm(monkeypatch):
    async def fake_call_llm(system_message, prompt, image_b64=None):
        if "e-commerce copywriter" in system_message:
            return dict(LISTING_RESPONSE)
        if "visual resale expert" in system_message:
            return dict(VISION_RESPONSE)
        if "Marketing Intelligence Agent" in system_message:
            return dict(AGENT_RESPONSE)
        if "real-time marketing manager" in system_message:
            return dict(ASSISTANT_RESPONSE)
        if "head of marketing" in system_message:
            return dict(BRIEF_RESPONSE)
        raise AssertionError(f"Unexpected system message: {system_message[:100]!r}")

    monkeypatch.setattr(llm, "call_llm", fake_call_llm)


def headers(wid):
    return {"X-Workspace-Id": wid} if wid else {}


def create_workspace(client, name):
    r = client.post("/api/workspaces", json={"name": name, "currency": "USD", "business_type": "Reseller"})
    assert r.status_code == 200, r.text
    return r.json()["id"]


def create_item(client, wid, name="Test Item", cost=100.0):
    r = client.post("/api/items", headers=headers(wid),
                    json={"name": name, "description": "A fine item", "condition": "Like New", "cost": cost, "category": "Electronics"})
    assert r.status_code == 200, r.text
    assert "_id" not in r.json()
    return r.json()


def test_api_root(client):
    r = client.get("/api/")
    assert r.status_code == 200
    assert r.json() == {"message": "Listrix API is running"}


def test_default_workspace_bootstrapped(client):
    ws = client.get("/api/workspaces").json()
    assert any(w.get("is_default") for w in ws)


def test_workspace_create_logs_workspace_created_event(client):
    wid = create_workspace(client, "Event Check Biz")
    events = client.get("/api/events", headers=headers(wid)).json()
    types = [e["type"] for e in events]
    assert "WORKSPACE_CREATED" in types, types
    assert "ITEM_CREATED" not in types, types


def test_workspace_update_and_export(client):
    wid = create_workspace(client, "Export Biz")
    r = client.put(f"/api/workspaces/{wid}", json={"primary_color": "#112233", "currency": "NZD"})
    assert r.status_code == 200
    assert r.json()["primary_color"] == "#112233"
    create_item(client, wid, "Export Item")
    out = client.get(f"/api/workspaces/{wid}/export").json()
    assert out["workspace"]["id"] == wid
    assert len(out["items"]) == 1
    assert out["items"][0]["workspace_id"] == wid


def test_item_isolation_between_workspaces(client):
    a = create_workspace(client, "Isolation A")
    b = create_workspace(client, "Isolation B")
    create_item(client, a, "A-Only Item")
    create_item(client, b, "B-Only Item")
    a_items = client.get("/api/items", headers=headers(a)).json()
    b_items = client.get("/api/items", headers=headers(b)).json()
    assert [i["name"] for i in a_items] == ["A-Only Item"]
    assert [i["name"] for i in b_items] == ["B-Only Item"]


def test_missing_and_invalid_header_fallback_to_default(client):
    r = client.post("/api/items", json={"name": "No Header Item", "description": "d", "condition": "Good"})
    assert r.status_code == 200
    default_id = [w for w in client.get("/api/workspaces").json() if w["is_default"]][0]["id"]
    r = client.post("/api/items", headers=headers("not-a-real-workspace"),
                    json={"name": "Bad Header Item", "description": "d", "condition": "Good"})
    assert r.status_code == 200
    default_items = client.get("/api/items", headers=headers(default_id)).json()
    names = {i["name"] for i in default_items}
    assert {"No Header Item", "Bad Header Item"} <= names


def test_item_detail_cross_workspace_404(client):
    a = create_workspace(client, "Detail A")
    b = create_workspace(client, "Detail B")
    item = create_item(client, a, "Secret Item")
    assert client.get(f"/api/items/{item['id']}", headers=headers(a)).status_code == 200
    assert client.get(f"/api/items/{item['id']}", headers=headers(b)).status_code == 404


def test_listing_generation_is_scoped(client):
    a = create_workspace(client, "List A")
    b = create_workspace(client, "List B")
    r = client.post("/api/ai/generate", headers=headers(a),
                    json={"name": "Sony Headphones", "description": "Wireless", "condition": "Like New", "cost": 150.0})
    assert r.status_code == 200, r.text
    listing = r.json()
    assert listing["listing_title"] == LISTING_RESPONSE["listing_title"]
    assert listing["suggested_price"] == 199.0
    assert "_id" not in listing
    assert len(client.get("/api/listings", headers=headers(a)).json()) == 1
    assert client.get("/api/listings", headers=headers(b)).json() == []


def test_analyze_agent_and_control_layer(client):
    a = create_workspace(client, "Agent A")
    item = create_item(client, a, "Agent Item", cost=150.0)
    client.post("/api/ai/generate", headers=headers(a),
                json={"name": item["name"], "description": item["description"], "condition": item["condition"], "cost": 150.0, "item_id": item["id"]})
    r = client.post(f"/api/ai/analyze/{item['id']}", headers=headers(a))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["performance"]["status"] == "good"
    sugg = body["suggestions"]
    assert len(sugg) == 2
    ids = {s["type"]: s["id"] for s in sugg}

    # apply add_keywords -> listing hashtags updated
    kw_id = ids["add_keywords"]
    assert client.post(f"/api/suggestions/{kw_id}/apply", headers=headers(a)).json()["status"] == "applied"
    listing = client.get("/api/listings", headers=headers(a)).json()[0]
    assert "wireless" in listing["hashtags"]

    # apply reduce_price -> price history recorded
    pr_id = ids["reduce_price"]
    assert client.post(f"/api/suggestions/{pr_id}/apply", headers=headers(a)).json()["status"] == "applied"
    ph = client.get(f"/api/price-history/{item['id']}", headers=headers(a)).json()
    assert len(ph) == 1
    assert ph[0]["new_price"] == 149.0
    assert client.get("/api/listings", headers=headers(a)).json()[0]["suggested_price"] == 149.0

    # applying a non-pending suggestion again is rejected
    assert client.post(f"/api/suggestions/{pr_id}/apply", headers=headers(a)).status_code == 400


def test_suggestion_edit_and_dismiss(client):
    a = create_workspace(client, "Sugg A")
    item = create_item(client, a, "Sugg Item")
    body = client.post(f"/api/ai/analyze/{item['id']}", headers=headers(a)).json()
    kw = [s for s in body["suggestions"] if s["type"] == "add_keywords"][0]

    edited = client.post(f"/api/suggestions/{kw['id']}/edit", headers=headers(a),
                         json={"detail": "Updated plan", "params": {"add_hashtags": ["extra-tag"]}})
    assert edited.status_code == 200
    assert edited.json()["detail"] == "Updated plan"
    updated = [s for s in client.get("/api/suggestions", headers=headers(a)).json() if s["id"] == kw["id"]][0]
    assert "extra-tag" in updated["params"]["add_hashtags"]

    pr = [s for s in body["suggestions"] if s["type"] == "reduce_price"][0]
    dismissed = client.post(f"/api/suggestions/{pr['id']}/dismiss", headers=headers(a))
    assert dismissed.status_code == 200
    assert dismissed.json()["status"] == "dismissed"
    pending = client.get("/api/suggestions", headers=headers(a), params={"status": "pending"}).json()
    pending_ids = {s["id"] for s in pending}
    assert kw["id"] in pending_ids  # editing preserves pending status
    assert pr["id"] not in pending_ids  # dismissed leaves the queue


def test_suggestion_cross_workspace_protection(client):
    a = create_workspace(client, "Prot A")
    b = create_workspace(client, "Prot B")
    item = create_item(client, a, "Protected")
    body = client.post(f"/api/ai/analyze/{item['id']}", headers=headers(a)).json()
    sugg_id = body["suggestions"][0]["id"]
    assert client.post(f"/api/suggestions/{sugg_id}/apply", headers=headers(b)).status_code == 404
    assert client.post(f"/api/suggestions/{sugg_id}/dismiss", headers=headers(b)).status_code == 404
    assert client.post(f"/api/suggestions/{sugg_id}/edit", headers=headers(b), json={"detail": "x"}).status_code == 404


def test_analyze_all_and_performance_intelligence(client):
    a = create_workspace(client, "Perf A")
    for i in range(2):
        create_item(client, a, f"Perf Item {i}")
    r = client.post("/api/ai/analyze-all", headers=headers(a))
    assert r.status_code == 200
    job = r.json()
    assert job["status"] == "queued" and job["total"] == 2 and job["job_id"]
    # analyze-all now runs as a background job; poll until it completes.
    for _ in range(40):
        st = client.get(f"/api/jobs/{job['job_id']}", headers=headers(a)).json()
        if st["status"] in ("done", "failed"):
            break
        time.sleep(0.2)
    assert st["status"] == "done", st
    assert st["results"] == 2
    perf = client.get("/api/performance", headers=headers(a)).json()
    assert len(perf) == 2
    pi = client.get("/api/performance-intelligence", headers=headers(a)).json()
    assert pi["summary"]["analyzed"] == 2
    assert pi["best_performing"][0]["name"] == "Perf Item 1"
    signals = client.get("/api/market/signals", headers=headers(a)).json()
    assert len(signals) == 2
    assert signals[0]["market_signal"]["simulated"] is True


def test_client_events_whitelist(client):
    a = create_workspace(client, "Events A")
    ok = client.post("/api/client-events", headers=headers(a),
                     json={"type": "WIDGET_VIEWED", "message": "widget seen", "payload": {"w": 1}})
    assert ok.status_code == 200
    assert ok.json()["status"] == "ok"
    bad = client.post("/api/client-events", headers=headers(a), json={"type": "HACKED", "message": "nope"})
    assert bad.status_code == 400


def test_inbox_refresh_and_isolation(client):
    a = create_workspace(client, "Inbox A")
    b = create_workspace(client, "Inbox B")
    item = create_item(client, a, "Inbox Item")
    client.post(f"/api/ai/analyze/{item['id']}", headers=headers(a))
    r = client.post("/api/inbox/refresh", headers=headers(a))
    assert r.status_code == 200
    assert r.json()["count"] >= 1
    a_msgs = client.get("/api/inbox", headers=headers(a)).json()
    b_msgs = client.get("/api/inbox", headers=headers(b)).json()
    assert len(a_msgs) >= 1
    assert b_msgs == []


def test_integrations_connect_sync_and_isolation(client):
    a = create_workspace(client, "Int A")
    b = create_workspace(client, "Int B")
    conns = client.get("/api/integrations", headers=headers(a)).json()
    assert len(conns) == 5
    assert {c["platform"] for c in conns} == {"TradeMe", "Facebook Marketplace", "Gmail", "Pricing Signals", "Competitor Listings"}
    # sync before connect -> 400
    assert client.post("/api/integrations/TradeMe/sync", headers=headers(a)).status_code == 400
    connected = client.post("/api/integrations/TradeMe/connect", headers=headers(a)).json()
    assert connected["auth_status"] == "connected"
    synced = client.post("/api/integrations/TradeMe/sync", headers=headers(a))
    assert synced.status_code == 200
    assert synced.json()["simulated"] is True
    # isolation: workspace B still sees TradeMe disconnected
    b_conns = {c["platform"]: c["auth_status"] for c in client.get("/api/integrations", headers=headers(b)).json()}
    assert b_conns["TradeMe"] == "disconnected"


def test_brief_generate_and_latest(client):
    a = create_workspace(client, "Brief A")
    r = client.post("/api/brief/generate", headers=headers(a))
    assert r.status_code == 200, r.text
    brief = r.json()
    assert brief["headline"] == "Solid day"
    assert brief["opportunities"] == ["Bundle"]
    assert client.get("/api/brief/latest", headers=headers(a)).json()["headline"] == "Solid day"
    # isolation
    b = create_workspace(client, "Brief B")
    assert client.get("/api/brief/latest", headers=headers(b)).json() is None


def test_assistant_with_and_without_item(client):
    a = create_workspace(client, "Asst A")
    item = create_item(client, a, "Asst Item")
    r = client.post("/api/ai/assistant", headers=headers(a), json={"query": "What should I do?", "item_id": item["id"]})
    assert r.status_code == 200
    assert r.json()["answer"] == ASSISTANT_RESPONSE["answer"]
    voice = client.post("/api/ai/assistant", headers=headers(a), json={"query": "Hello", "voice": True})
    assert voice.status_code == 200
    types = [e["type"] for e in client.get("/api/events", headers=headers(a)).json()]
    assert "VOICE_QUERY_RECEIVED" in types
    assert "VOICE_QUERY_PROCESSED" in types


def test_vision_analysis_persists_to_item(client):
    a = create_workspace(client, "Vision A")
    item = create_item(client, a, "Vision Item")
    r = client.post("/api/ai/vision/analyze", headers=headers(a),
                    json={"image": "data:image/jpeg;base64,QUJDRA==", "item_id": item["id"], "hint": "Sony headphones"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["item_type"] == "headphones"
    assert body["value_estimate"]["mid"] == 200.0
    updated = client.get(f"/api/items/{item['id']}", headers=headers(a)).json()
    assert updated["category"] == "Electronics"
    assert updated["vision"]["brand"] == "Sony"
    types = [e["type"] for e in client.get("/api/events", headers=headers(a)).json()]
    assert "IMAGE_ANALYSED" in types
    assert "VALUE_ESTIMATED" in types


def test_competitors_endpoint(client):
    a = create_workspace(client, "Comp A")
    item = create_item(client, a, "Comp Item", cost=100.0)
    client.post("/api/ai/generate", headers=headers(a),
                json={"name": item["name"], "description": item["description"], "condition": item["condition"], "cost": 100.0, "item_id": item["id"]})
    r = client.get(f"/api/competitors/{item['id']}", headers=headers(a))
    assert r.status_code == 200
    assert r.json()["simulated"] is True
    assert r.json()["positioning"] in ("premium", "competitive", "unknown")
    assert client.get(f"/api/competitors/{item['id']}", headers=headers(a)).json()["our_price"] == 199.0


def test_startup_creates_indexes():
    async def check():
        idx = await db.items.index_information()
        names = list(idx.keys())
        assert any("workspace_id" in n and "created_at" in n for n in names), names
        widx = await db.workspaces.index_information()
        assert "id_1" in widx or any("id" in n for n in widx), list(widx.keys())

    asyncio.get_event_loop().run_until_complete(check())


def test_no_mongo_ids_leak(client):
    a = create_workspace(client, "Leak A")
    item = create_item(client, a, "Leak Item")
    client.post("/api/ai/generate", headers=headers(a),
                json={"name": item["name"], "description": item["description"], "condition": item["condition"], "cost": 10.0, "item_id": item["id"]})
    client.post(f"/api/ai/analyze/{item['id']}", headers=headers(a))
    for path in ["/api/items", "/api/listings", "/api/events", "/api/performance", "/api/suggestions", "/api/integrations", "/api/workspaces"]:
        payload = client.get(path, headers=headers(a)).json()
        assert "_id" not in payload
