"""Tests for the Month 4-6 platform layer: object storage + thumbnails, background
jobs (analyze-all), notifications, item stages, global search, CSV import, event
analytics, inbox reply drafts, and the opt-in scheduler tick."""
import asyncio
import base64
import io
import time
import uuid

import pytest
from fastapi.testclient import TestClient

import server
from deps import db
from services import llm

AGENT_RESPONSE = {
    "performance": {"status": "good", "likelihood_of_sale": 82, "reason": "Strong listing", "recommended_action": "Keep price"},
    "suggestions": [],
}


@pytest.fixture(scope="module")
def client():
    with TestClient(server.app) as c:
        yield c


@pytest.fixture(autouse=True)
def fake_llm(monkeypatch):
    async def fake_call_llm(system_message, prompt, image_b64=None):
        if "Marketing Intelligence Agent" in system_message:
            return dict(AGENT_RESPONSE)
        return {"listing_title": "T", "listing_description": "D", "suggested_price": 200.0, "hashtags": ["test"]}

    monkeypatch.setattr(llm, "call_llm", fake_call_llm)


def headers(wid):
    return {"X-Workspace-Id": wid} if wid else {}


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def create_workspace(client, name, **kw):
    payload = {"name": name}
    payload.update(kw)
    r = client.post("/api/workspaces", json=payload)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def create_item(client, wid, name="Test Item", cost=100.0, category="Electronics"):
    r = client.post("/api/items", headers=headers(wid), json={
        "name": name, "description": "A fine item", "condition": "Good", "cost": cost, "category": category})
    assert r.status_code == 200, r.text
    return r.json()


def make_jpeg_data_uri(width=600, height=400):
    import random
    from PIL import Image
    buf = io.BytesIO()
    img = Image.frombytes("RGB", (width, height), bytes(random.randrange(256) for _ in range(width * height * 3)))
    img.save(buf, format="JPEG")
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


# ---- object storage + thumbnails ------------------------------------------------
def test_image_upload_retrieval_thumb_and_isolation(client):
    a = create_workspace(client, "Img A")
    b = create_workspace(client, "Img B")
    item = create_item(client, a, "Photographed Item")
    uri = make_jpeg_data_uri()

    r = client.post(f"/api/items/{item['id']}/image", headers=headers(a), json={"data": uri})
    assert r.status_code == 200, r.text
    image_id = r.json()["image_id"]
    assert image_id and r.json()["id"] == item["id"]

    full = client.get(f"/api/images/{image_id}", headers=headers(a))
    assert full.status_code == 200
    assert full.headers["content-type"].startswith("image/jpeg")
    assert len(full.content) > 30_000  # noisy JPEG at 600x400 is large

    thumb = client.get(f"/api/images/{image_id}?thumb=1", headers=headers(a))
    assert thumb.status_code == 200
    assert len(thumb.content) < len(full.content)  # thumbnail is smaller

    assert client.get(f"/api/images/{image_id}", headers=headers(b)).status_code == 404
    assert client.post(f"/api/items/{item['id']}/image", headers=headers(a), json={"data": "not-base64!!"}).status_code == 400


def test_image_blob_not_stored_in_item_document(client):
    wid = create_workspace(client, "Img Compact")
    item = create_item(client, wid, "Compact Item")
    client.post(f"/api/items/{item['id']}/image", headers=headers(wid), json={"data": make_jpeg_data_uri()})
    doc = run(db.items.find_one({"id": item["id"], "workspace_id": wid}, {"_id": 0}))
    assert doc["image_id"]
    assert not (doc.get("image") or "").startswith("data:")
    blob = run(db.image_blobs.find_one({"id": doc["image_id"]}, {"_id": 0}))
    assert blob and blob["data"] and blob["thumb"]


# ---- background jobs ------------------------------------------------------------
def test_analyze_all_job_runs_to_done(client):
    wid = create_workspace(client, "Jobs")
    for i in range(2):
        create_item(client, wid, f"Job Item {i}")
    r = client.post("/api/ai/analyze-all", headers=headers(wid))
    assert r.status_code == 200
    job = r.json()
    assert job["status"] == "queued" and job["total"] == 2

    state = {}
    for _ in range(60):
        state = client.get(f"/api/jobs/{job['job_id']}", headers=headers(wid)).json()
        if state["status"] in ("done", "failed"):
            break
        time.sleep(0.2)
    assert state["status"] == "done", state
    assert state["results"] == 2 and state["done"] == 2

    # cross-workspace job access is forbidden
    other = create_workspace(client, "Jobs Other")
    assert client.get(f"/api/jobs/{job['job_id']}", headers=headers(other)).status_code == 404


def test_analyze_all_empty_returns_done_without_job(client):
    wid = create_workspace(client, "Jobs Empty")
    r = client.post("/api/ai/analyze-all", headers=headers(wid)).json()
    assert r == {"job_id": None, "status": "done", "total": 0, "analyzed": 0}


def test_scheduled_tick_enqueues_jobs(client):
    wid = create_workspace(client, "Scheduler")
    create_item(client, wid, "Scheduled Item")
    from services.scheduler import run_scheduled_tick
    run(run_scheduled_tick())
    jobs = []
    for _ in range(40):
        jobs = run(db.jobs.find({"workspace_id": wid, "kind": "scheduled-analyze"}, {"_id": 0}).to_list(10))
        if jobs and jobs[0].get("status") in ("done", "failed"):
            break
        time.sleep(0.2)
    assert jobs, "scheduled tick should have created a job"
    assert jobs[0]["total"] == 1


# ---- notifications ---------------------------------------------------------------
def test_notifications_created_and_mark_read(client):
    wid = create_workspace(client, "Ntfy")
    item = create_item(client, wid, "Notifiable Item")
    client.post(f"/api/items/{item['id']}/mark-sold", headers=headers(wid), json={"sale_price": 100.0})
    client.post(f"/api/items/{item['id']}/stage", headers=headers(wid), json={"stage": "archived"})
    notes = client.get("/api/notifications", headers=headers(wid)).json()
    kinds = {n["kind"] for n in notes}
    assert "sale" in kinds and "stage" in kinds
    unread = client.get("/api/notifications?unread=1", headers=headers(wid)).json()
    assert len(unread) >= 2
    r = client.post("/api/notifications/read", headers=headers(wid))
    assert r.json()["marked"] >= 2
    assert client.get("/api/notifications?unread=1", headers=headers(wid)).json() == []


# ---- item stages ------------------------------------------------------------------
def test_item_stage_transitions(client):
    wid = create_workspace(client, "Stages")
    item = create_item(client, wid, "Stage Item")
    assert item["stage"] == "inventory"

    def set_stage(stage):
        return client.post(f"/api/items/{item['id']}/stage", headers=headers(wid), json={"stage": stage})

    assert set_stage("listed").status_code == 200
    assert set_stage("sold").json()["stage"] == "sold"
    assert set_stage("listed").status_code == 400  # sold -> listed is not allowed
    assert set_stage("archived").json()["stage"] == "archived"  # sold -> archived allowed
    assert set_stage("listed").json()["stage"] == "listed"  # archived -> listed allowed
    assert set_stage("inventory").json()["stage"] == "inventory"  # listed -> inventory allowed
    assert set_stage("bogus").status_code == 400
    assert set_stage("listed").status_code == 200

    # mark-sold / mark-unsold keep stage consistent
    client.post(f"/api/items/{item['id']}/mark-sold", headers=headers(wid), json={"sale_price": 90.0})
    assert client.get(f"/api/items/{item['id']}", headers=headers(wid)).json()["stage"] == "sold"
    client.post(f"/api/items/{item['id']}/mark-unsold", headers=headers(wid))
    got = client.get(f"/api/items/{item['id']}", headers=headers(wid)).json()
    assert got["stage"] == "inventory"  # no listing exists -> inventory

    other = create_workspace(client, "Stages Other")
    assert client.post(f"/api/items/{item['id']}/stage", headers=headers(other), json={"stage": "listed"}).status_code == 404


# ---- global search ----------------------------------------------------------------
def test_global_search_scoped(client):
    a = create_workspace(client, "Search A")
    b = create_workspace(client, "Search B")
    create_item(client, a, "Sony WH-1000XM4 Headphones", category="Electronics")
    create_item(client, b, "Sony PlayStation Console", category="Gaming")
    create_item(client, a, "Random Lamp", category="Furniture")

    res = client.get("/api/search", params={"q": "sony"}, headers=headers(a)).json()
    items_hit = [r for r in res["results"] if r["type"] == "item"]
    assert items_hit == [{"type": "item", "id": res["results"][0]["id"], "title": "Sony WH-1000XM4 Headphones", "subtitle": "Electronics", "link": "/items/" + res["results"][0]["id"]}]

    res_b = client.get("/api/search", params={"q": "sony"}, headers=headers(b)).json()
    assert [r["title"] for r in res_b["results"] if r["type"] == "item"] == ["Sony PlayStation Console"]

    assert client.get("/api/search", params={"q": "s"}, headers=headers(a)).json()["count"] == 0  # too short


# ---- CSV import --------------------------------------------------------------------
def test_csv_import(client):
    wid = create_workspace(client, "Import")
    other = create_workspace(client, "Import Other")
    csv_text = (
        "name,description,condition,cost,category\n"
        "Good Item,Brand new,New,25.5,Electronics\n"
        ",No name here,Good,10,Household\n"
        "Bad Cost Item,oops,Good,abc,Furniture\n"
        "Another Good Item,,Like New,,Sport\n"
    )
    r = client.post("/api/workspaces/import", headers=headers(wid), json={"csv": csv_text})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["imported"] == 2
    assert body["skipped"] == 2
    assert len(body["errors"]) == 2

    names = {i["name"] for i in client.get("/api/items", headers=headers(wid)).json()}
    assert {"Good Item", "Another Good Item"} <= names
    assert client.get("/api/items", headers=headers(other)).json() == []
    types = [e["type"] for e in client.get("/api/events", headers=headers(wid)).json()]
    assert "ITEMS_IMPORTED" in types


# ---- event analytics ----------------------------------------------------------------
def test_event_analytics(client):
    wid = create_workspace(client, "Analytics")
    item = create_item(client, wid, "Analytics Item")
    client.post(f"/api/items/{item['id']}/mark-sold", headers=headers(wid), json={"sale_price": 60.0})
    a = client.get("/api/analytics", headers=headers(wid)).json()
    assert a["totals"]["items"] == 1
    assert a["totals"]["sold"] == 1
    assert a["events_total"] >= 2
    types = {t["type"] for t in a["top_event_types"]}
    assert "ITEM_CREATED" in types and "ITEM_SOLD" in types
    assert a["events_by_day"] and a["events_by_day"][0]["count"] >= 1


# ---- inbox reply drafts ---------------------------------------------------------------
def test_inbox_reply_draft_and_read(client):
    wid = create_workspace(client, "Replies")
    create_item(client, wid, "Reply Item")
    client.post("/api/inbox/refresh", headers=headers(wid))
    msgs = client.get("/api/inbox", headers=headers(wid)).json()
    assert msgs
    mid = msgs[0]["id"]

    r = client.post(f"/api/inbox/{mid}/reply", headers=headers(wid), json={"text": "Hi! Yes it is available."})
    assert r.status_code == 200
    assert r.json()["reply_draft"] == "Hi! Yes it is available."

    assert client.post(f"/api/inbox/{mid}/reply", headers=headers(wid), json={"text": "   "}).status_code == 400
    client.post(f"/api/inbox/{mid}/read", headers=headers(wid))
    got = [m for m in client.get("/api/inbox", headers=headers(wid)).json() if m["id"] == mid][0]
    assert got["read"] is True and got["reply_draft"]

    other = create_workspace(client, "Replies Other")
    assert client.post(f"/api/inbox/{mid}/reply", headers=headers(other), json={"text": "hi"}).status_code == 404
