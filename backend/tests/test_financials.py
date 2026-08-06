"""Financials endpoint tests: profit/fees/tax/margin math, value-estimate
fallback for unlisted items, workspace isolation, currency passthrough."""
import asyncio
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

import server
from deps import db


@pytest.fixture(scope="module")
def client():
    with TestClient(server.app) as c:
        yield c


def headers(wid):
    return {"X-Workspace-Id": wid} if wid else {}


def create_workspace(client, name, **kw):
    payload = {"name": name, "currency": "USD", "business_type": "Reseller"}
    payload.update(kw)
    r = client.post("/api/workspaces", json=payload)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def create_item(client, wid, name="Test Item", cost=100.0, category="Electronics", value_estimate=None):
    payload = {
        "name": name, "description": "A fine item", "condition": "Good",
        "cost": cost, "category": category,
    }
    if value_estimate is not None:
        payload["value_estimate"] = value_estimate
    r = client.post("/api/items", headers=headers(wid), json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def insert_listing(wid, item_id, price):
    run(db.listings.insert_one({
        "id": str(uuid.uuid4()), "workspace_id": wid, "item_id": item_id,
        "source_name": "Seed", "listing_title": "Seed listing",
        "listing_description": "Seeded for financials test", "suggested_price": price,
        "hashtags": [], "created_at": datetime.now(timezone.utc).isoformat(),
    }))


def get_financials(client, wid):
    r = client.get("/api/financials", headers=headers(wid))
    assert r.status_code == 200, r.text
    return r.json()


def test_financials_math_and_value_estimate_fallback(client):
    wid = create_workspace(client, "Financials Math", tax_rate=10.0, currency="USD")
    listed = create_item(client, wid, "Listed Item", cost=100.0, category="Electronics")
    unlisted = create_item(client, wid, "Unlisted Item", cost=50.0, category="Furniture",
                           value_estimate={"low": 60.0, "mid": 80.0, "high": 100.0})
    insert_listing(wid, listed["id"], 200.0)

    fin = get_financials(client, wid)
    assert fin["currency"] == "USD"
    assert fin["marketplace_fee_rate"] == 0.079
    assert fin["tax_rate"] == 0.10
    assert "potential" in fin["note"].lower()

    assert fin["totals"]["items"] == 2
    assert fin["totals"]["listed"] == 1
    assert fin["totals"]["invested"] == 150.0
    assert fin["totals"]["potential_revenue"] == 280.0

    by_id = {r["item_id"]: r for r in fin["items"]}

    listed_row = by_id[listed["id"]]
    assert listed_row["price"] == 200.0
    assert listed_row["listed"] is True
    assert listed_row["gross_profit"] == 100.0
    assert listed_row["estimated_fees"] == 15.80
    assert listed_row["estimated_tax"] == 10.0
    assert listed_row["net_profit"] == 74.20
    assert listed_row["margin_pct"] == 37.1

    unlisted_row = by_id[unlisted["id"]]
    assert unlisted_row["price"] == 80.0  # falls back to value_estimate.mid
    assert unlisted_row["listed"] is False
    assert unlisted_row["estimated_fees"] == 6.32
    assert unlisted_row["net_profit"] == 20.68
    assert unlisted_row["margin_pct"] == 25.9

    assert fin["totals"]["net_profit"] == 94.88
    assert fin["totals"]["net_margin_pct"] == 33.9

    cats = {c["category"]: c for c in fin["by_category"]}
    assert cats["Electronics"]["count"] == 1
    assert cats["Electronics"]["net_profit"] == 74.20
    assert cats["Furniture"]["net_profit"] == 20.68


def test_financials_workspace_isolation(client):
    a = create_workspace(client, "Fin Iso A")
    b = create_workspace(client, "Fin Iso B")
    create_item(client, a, "A Costly", cost=500.0)
    create_item(client, b, "B Cheap", cost=1.0)

    fa = get_financials(client, a)
    fb = get_financials(client, b)
    assert fa["totals"]["invested"] == 500.0
    assert fb["totals"]["invested"] == 1.0
    assert len(fa["items"]) == 1
    assert fa["items"][0]["name"] == "A Costly"


def test_financials_currency_passthrough_and_default_tax(client):
    wid = create_workspace(client, "NZD Shop", currency="NZD")
    create_item(client, wid, "Kiwi Item", cost=100.0,
                value_estimate={"low": 150.0, "mid": 200.0, "high": 250.0})

    fin = get_financials(client, wid)
    assert fin["currency"] == "NZD"
    assert fin["tax_rate"] == 0.0  # not configured
    assert fin["totals"]["potential_revenue"] == 200.0
    assert fin["totals"]["net_profit"] == 84.20  # 200 - 100 - 15.80 fees


def test_financials_skips_items_without_cost_or_price(client):
    wid = create_workspace(client, "Empty Fin Shop")
    create_item(client, wid, "No Numbers", cost=None, value_estimate=None)
    fin = get_financials(client, wid)
    assert fin["totals"]["items"] == 0
    assert fin["totals"]["potential_revenue"] == 0.0
    assert fin["items"] == []


def test_mark_sold_endpoint_and_event(client):
    wid = create_workspace(client, "Sales Flow")
    item = create_item(client, wid, "Sold Item", cost=100.0)
    r = client.post(f"/api/items/{item['id']}/mark-sold", headers=headers(wid), json={"sale_price": 220.0})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["sold"] is True
    assert body["sale_price"] == 220.0
    assert body["sold_at"]

    got = client.get(f"/api/items/{item['id']}", headers=headers(wid)).json()
    assert got["sold"] is True and got["sale_price"] == 220.0

    types = [e["type"] for e in client.get("/api/events", headers=headers(wid)).json()]
    assert "ITEM_SOLD" in types


def test_mark_sold_validation_and_isolation(client):
    a = create_workspace(client, "Sales A")
    b = create_workspace(client, "Sales B")
    item = create_item(client, a, "Private Item", cost=10.0)

    r = client.post(f"/api/items/{item['id']}/mark-sold", headers=headers(a), json={"sale_price": -1})
    assert r.status_code == 422

    r = client.post(f"/api/items/{item['id']}/mark-sold", headers=headers(b), json={"sale_price": 50})
    assert r.status_code == 404
    assert client.get(f"/api/items/{item['id']}", headers=headers(a)).json()["sold"] is False


def test_mark_unsold_reverts_sale(client):
    wid = create_workspace(client, "Sales Revert")
    item = create_item(client, wid, "Reverted Item", cost=40.0)
    client.post(f"/api/items/{item['id']}/mark-sold", headers=headers(wid), json={"sale_price": 80.0})
    r = client.post(f"/api/items/{item['id']}/mark-unsold", headers=headers(wid))
    assert r.status_code == 200, r.text
    assert r.json()["sold"] is False and r.json()["sale_price"] is None

    types = [e["type"] for e in client.get("/api/events", headers=headers(wid)).json()]
    assert "ITEM_UNSOLD" in types


def test_financials_realized_vs_potential(client):
    wid = create_workspace(client, "Realized Fin", tax_rate=10.0, currency="USD")
    sold = create_item(client, wid, "Sold Goods", cost=100.0, category="Electronics")
    open_item = create_item(client, wid, "Open Goods", cost=100.0, category="Furniture",
                            value_estimate={"low": 150.0, "mid": 200.0, "high": 250.0})
    client.post(f"/api/items/{sold['id']}/mark-sold", headers=headers(wid), json={"sale_price": 220.0})

    fin = get_financials(client, wid)
    t = fin["totals"]
    assert t["sold"] == 1
    assert t["invested"] == 200.0

    # Realized: 220 sale -> fees 17.38, gross 120, tax 12, net 90.62, margin 41.2%
    assert t["realized_revenue"] == 220.0
    assert t["realized_fees"] == 17.38
    assert t["realized_tax"] == 12.0
    assert t["realized_net_profit"] == 90.62
    assert t["realized_margin_pct"] == 41.2

    # Potential: unsold estimate 200, 10% tax -> net 74.20
    assert t["potential_revenue"] == 200.0
    assert t["potential_net_profit"] == 74.20

    assert t["net_profit"] == 164.82
    assert t["net_margin_pct"] == 39.2

    by_id = {r["item_id"]: r for r in fin["items"]}
    sold_row = by_id[sold["id"]]
    assert sold_row["status"] == "sold"
    assert sold_row["sale_price"] == 220.0
    assert sold_row["price"] == 220.0
    assert sold_row["net_profit"] == 90.62
    assert by_id[open_item["id"]]["status"] == "unlisted"

    cats = {c["category"]: c for c in fin["by_category"]}
    assert cats["Electronics"]["sold"] == 1
    assert cats["Furniture"]["sold"] == 0
