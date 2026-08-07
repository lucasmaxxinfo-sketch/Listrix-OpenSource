"""Stocksix inventory connector.

Pulls inventory from the owner's Stocksix hub (local-first, open source) through its
public API: `GET {base_url}/api/public/v1/inventory` with a bearer key.

Sync is a user-initiated inventory import (not AI): it creates missing Listrix items
and updates price/category/description on existing ones, then logs the result. It never
posts, prices, or modifies anything outside the workspace.
"""
import asyncio
import logging
import uuid
from datetime import datetime, timezone

import requests

import config
from deps import db
from services.events import EventType, log_event
from services.integrations.base import ConnectorAdapter, EncryptedTokenMixin
from services.integrations.creds import creds_configured, resolve_creds

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://localhost:3000"
SYNC_MAX_ITEMS = 1000


class StocksixAdapter(EncryptedTokenMixin, ConnectorAdapter):
    platform = "Stocksix"
    simulated = False

    def is_configured(self) -> bool:
        return bool(config.STOCKSIX_API_KEY)

    def _base_url(self, creds=None):
        creds = creds or {}
        return (creds.get("base_url") or config.STOCKSIX_BASE_URL or DEFAULT_BASE_URL).strip().rstrip("/")

    def _headers(self, creds=None):
        creds = creds or {}
        return {
            "Authorization": f"Bearer {creds.get('api_key') or config.STOCKSIX_API_KEY}",
            "Accept": "application/json",
        }

    def _fetch_inventory(self, creds, limit=SYNC_MAX_ITEMS):
        r = requests.get(
            f"{self._base_url(creds)}/api/public/v1/inventory",
            headers=self._headers(creds),
            params={"limit": limit},
            timeout=15,
        )
        r.raise_for_status()
        return r.json().get("items", [])

    # ---- live connection test (Connection Wizard) ---------------------------------
    async def test(self, workspace_id: str, conn: dict = None) -> dict:
        creds = await resolve_creds(self.platform, workspace_id)
        if not creds_configured(creds, self.platform):
            return {"ok": False, "message": "Missing Stocksix address or API key. Add them in the wizard first."}
        try:
            items = await asyncio.to_thread(self._fetch_inventory, creds, 1)
            return {"ok": True, "message": f"Stocksix accepted the key — inventory is reachable ({len(items)}+ rows)."}
        except Exception as e:
            logger.warning("Stocksix connection test failed: %s", e)
            return {"ok": False, "message": f"Stocksix rejected the request: {e}"}

    # ---- adapter interface ---------------------------------------------------------
    async def connect(self, workspace_id: str, conn: dict) -> dict:
        creds = await resolve_creds(self.platform, workspace_id)
        await db.integrations.update_one(
            {"platform": self.platform, "workspace_id": workspace_id},
            {"$set": {"auth_status": "connected", "sync_enabled": True,
                      "tokens": self._encrypt({"base_url": self._base_url(creds), "api_key": creds.get("api_key")})}},
        )
        await log_event(workspace_id, EventType.CONNECTOR_AUTH_SUCCESS,
                        f"Connected to {self.platform}", {"platform": self.platform})
        return {"platform": self.platform, "auth_status": "connected",
                "note": "Stocksix link is live. Press Sync to import your inventory into this business."}

    async def sync(self, workspace_id: str, conn: dict) -> dict:
        creds = await resolve_creds(self.platform, workspace_id)
        rows = await asyncio.to_thread(self._fetch_inventory, creds)
        existing = {
            i.get("external_ref"): i
            for i in await db.items.find(
                {"workspace_id": workspace_id, "source": "stocksix"}, {"_id": 0}
            ).to_list(5000)
            if i.get("external_ref")
        }
        now = datetime.now(timezone.utc)
        created = updated = skipped = 0
        for row in rows:
            ref = row.get("id") or row.get("sku") or row.get("barcode")
            if not ref:
                skipped += 1
                continue
            name = (row.get("name") or "Stocksix item").strip()[:120]
            qty = row.get("quantity")
            price = row.get("price")
            parts = []
            if qty is not None:
                parts.append(f"Qty: {qty}")
            if row.get("category"):
                parts.append(f"Category: {row['category']}")
            if row.get("location"):
                parts.append(f"Location: {row['location']}")
            if row.get("sku"):
                parts.append(f"SKU: {row['sku']}")
            if row.get("barcode"):
                parts.append(f"Barcode: {row['barcode']}")
            desc = ", ".join(parts) or f"Synced from Stocksix ({ref})"
            if ref in existing:
                item = existing[ref]
                patch = {}
                if price is not None and price != item.get("cost"):
                    patch["cost"] = price
                if row.get("category") and row.get("category") != item.get("category"):
                    patch["category"] = row["category"]
                if desc and desc != item.get("description"):
                    patch["description"] = desc
                if qty is not None and qty != item.get("stock_qty"):
                    patch["stock_qty"] = qty
                if patch:
                    patch["synced_at"] = now.isoformat()
                    await db.items.update_one({"id": item["id"], "workspace_id": workspace_id}, {"$set": patch})
                updated += 1
            else:
                await db.items.insert_one({
                    "id": str(uuid.uuid4()),
                    "workspace_id": workspace_id,
                    "name": name,
                    "description": desc,
                    "condition": (row.get("condition") or "Good").strip() or "Good",
                    "image": None,
                    "image_id": None,
                    "cost": float(price) if price is not None else None,
                    "category": row.get("category"),
                    "external_ref": ref,
                    "source": "stocksix",
                    "stock_qty": qty,
                    "stage": "inventory",
                    "sold": False,
                    "created_at": now.isoformat(),
                    "listed_at": now.isoformat(),
                })
                created += 1
        last_sync = now.isoformat()
        await db.integrations.update_one(
            {"platform": self.platform, "workspace_id": workspace_id}, {"$set": {"last_sync": last_sync}}
        )
        await log_event(workspace_id, EventType.CONNECTOR_SYNC_EXECUTED,
                        f"Stocksix sync: {created} created, {updated} updated",
                        {"platform": self.platform, "created": created, "updated": updated, "skipped": skipped})
        return {"platform": self.platform, "last_sync": last_sync,
                "items_created": created, "items_updated": updated, "items_skipped": skipped,
                "note": "Inventory imported into this business. These items are ready for AI listing generation."}
