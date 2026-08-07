"""Stocksix connector tests: wizard credential flow, inventory sync (create/update),
idempotency, and the AI status probe endpoint."""
import asyncio

import pytest
from fastapi.testclient import TestClient

import server
from deps import db

ENCRYPTION_KEY = "imyxa9xOJ1pCmSTezmMVwTnrJSzkTvxZozAKZN7i-4I="


@pytest.fixture(scope="module")
def client():
    with TestClient(server.app) as c:
        yield c


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Never hit a real Stocksix server in tests."""
    from services.integrations import stocksix

    def fake_fetch(self, creds, limit=1000):
        return [
            {"id": "11111111-1111-1111-1111-111111111111", "sku": "VCR-001", "barcode": "1234567890128",
             "name": "VCR Player", "quantity": 3, "price": 89.0, "category": "Electronics",
             "condition": "Good", "location": "Shelf A", "updated_at": "2026-08-07T00:00:00Z"},
            {"id": "22222222-2222-2222-2222-222222222222", "sku": "RM-042", "name": "Universal Remote",
             "quantity": 1, "price": 19.0, "category": "Accessories", "condition": "New",
             "location": "Shelf B", "updated_at": "2026-08-07T00:00:00Z"},
        ]

    monkeypatch.setattr(stocksix.StocksixAdapter, "_fetch_inventory", fake_fetch)
    import config

    monkeypatch.setattr(config, "CONNECTOR_ENCRYPTION_KEY", ENCRYPTION_KEY)


def headers(wid):
    return {"X-Workspace-Id": wid}


def make_workspace(client, name="Stocksix Biz"):
    r = client.post("/api/workspaces", json={"name": name})
    assert r.status_code == 200
    return r.json()["id"]


def test_stocksix_connector_seeded(client):
    wid = make_workspace(client)
    conns = client.get("/api/integrations", headers=headers(wid)).json()
    stock = next(c for c in conns if c["platform"] == "Stocksix")
    assert stock["kind"] == "inventory"
    assert stock["auth_status"] == "disconnected"
    assert "tokens" not in stock and "config" not in stock


def test_stocksix_wizard_save_connect_and_sync(client):
    wid = make_workspace(client)
    saved = client.post("/api/integrations/Stocksix/config", headers=headers(wid),
                        json={"credentials": {"base_url": "http://localhost:3000", "api_key": "stocksix-test-key-1234567890"}})
    assert saved.status_code == 200
    assert saved.json()["configured"] is True

    tested = client.post("/api/integrations/Stocksix/test", headers=headers(wid))
    assert tested.status_code == 200
    assert tested.json()["ok"] is True

    connected = client.post("/api/integrations/Stocksix/connect", headers=headers(wid))
    assert connected.status_code == 200
    assert connected.json()["auth_status"] == "connected"

    synced = client.post("/api/integrations/Stocksix/sync", headers=headers(wid))
    assert synced.status_code == 200
    assert synced.json()["items_created"] == 2
    assert synced.json()["items_updated"] == 0

    items = client.get("/api/items", headers=headers(wid)).json()
    assert {i["name"] for i in items} == {"VCR Player", "Universal Remote"}
    vcr = next(i for i in items if i["name"] == "VCR Player")
    assert vcr["cost"] == 89.0
    assert vcr["source"] == "stocksix"
    assert vcr["external_ref"] == "11111111-1111-1111-1111-111111111111"
    assert vcr["stock_qty"] == 3


def test_stocksix_sync_is_idempotent_and_updates(client):
    wid = make_workspace(client)
    client.post("/api/integrations/Stocksix/config", headers=headers(wid),
                json={"credentials": {"base_url": "http://localhost:3000", "api_key": "stocksix-test-key-1234567890"}})
    client.post("/api/integrations/Stocksix/connect", headers=headers(wid))
    client.post("/api/integrations/Stocksix/sync", headers=headers(wid))
    second = client.post("/api/integrations/Stocksix/sync", headers=headers(wid)).json()
    assert second["items_created"] == 0
    assert second["items_updated"] == 2  # price/qty/description already match -> still counted as seen
    assert client.get("/api/items", headers=headers(wid)).json().__len__() == 2


def test_ai_status_endpoint_reports_offline_gracefully(client, monkeypatch):
    wid = make_workspace(client)
    from services import llm

    async def offline():
        return {"ok": False, "detail": "connection refused"}

    monkeypatch.setattr(llm, "probe_llm", offline)
    status = client.get("/api/ai/status", headers=headers(wid)).json()
    assert status["reachable"] is False
    assert "connection refused" in status["detail"]

    async def online():
        return {"ok": True, "detail": "AI model is reachable"}

    monkeypatch.setattr(llm, "probe_llm", online)
    status = client.get("/api/ai/status", headers=headers(wid)).json()
    assert status["reachable"] is True
