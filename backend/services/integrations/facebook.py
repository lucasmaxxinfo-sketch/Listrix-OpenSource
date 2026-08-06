"""Real Facebook Marketplace connector (Graph API, page token).

Token-based (no OAuth dance): connect() stores the page token encrypted at rest and
sync() reads the page's marketplace listings, mapping lower external anchors to
PENDING (approval-gated) reduce_price suggestions. Never posts or mutates listings.
"""
import asyncio
import logging
from datetime import datetime, timezone

import config
import requests
from deps import db
from models import Suggestion
from services.events import EventType, log_event
from services.integrations.base import ConnectorAdapter, EncryptedTokenMixin
from services.integrations.creds import creds_configured, resolve_creds

logger = logging.getLogger(__name__)

GRAPH_URL = "https://graph.facebook.com/v21.0"
SYNC_MAX_ITEMS = 100


class FacebookAdapter(EncryptedTokenMixin, ConnectorAdapter):
    platform = "Facebook Marketplace"
    simulated = False

    def is_configured(self) -> bool:
        return bool(config.FACEBOOK_PAGE_TOKEN)

    def _headers(self, creds=None):
        creds = creds or {}
        return {"Authorization": f"Bearer {creds.get('page_token') or config.FACEBOOK_PAGE_TOKEN}"}

    # ---- network helpers (patchable in tests) ------------------------------------
    def _fetch_listings(self, creds=None):
        creds = creds or {}
        page_id = creds.get("page_id") or config.FACEBOOK_PAGE_ID or "me"
        r = requests.get(f"{GRAPH_URL}/{page_id}/marketplace_listings", headers=self._headers(creds), timeout=15)
        r.raise_for_status()
        return r.json().get("data", [])

    # ---- live connection test (used by the Connection Wizard) -----------------------
    async def test(self, workspace_id: str, conn: dict = None) -> dict:
        creds = await resolve_creds(self.platform, workspace_id)
        if not creds_configured(creds, self.platform):
            return {"ok": False, "message": "Missing Facebook page token. Add it in the wizard first."}
        try:
            page_id = creds.get("page_id") or "me"
            r = await asyncio.to_thread(
                lambda: requests.get(f"{GRAPH_URL}/{page_id}", headers=self._headers(creds), timeout=15))
            r.raise_for_status()
            return {"ok": True, "message": "Facebook accepted your page token."}
        except Exception as e:
            logger.warning(f"Facebook connection test failed: {e}")
            return {"ok": False, "message": f"Facebook rejected the token: {e}"}

    # ---- adapter interface -------------------------------------------------------
    async def connect(self, workspace_id: str, conn: dict) -> dict:
        creds = await resolve_creds(self.platform, workspace_id)
        await db.integrations.update_one(
            {"platform": self.platform, "workspace_id": workspace_id},
            {"$set": {"auth_status": "connected", "sync_enabled": True,
                      "tokens": self._encrypt({"token": creds.get("page_token") or config.FACEBOOK_PAGE_TOKEN})}},
        )
        await log_event(workspace_id, EventType.CONNECTOR_AUTH_SUCCESS, f"Connected to {self.platform}", {"platform": self.platform})
        return {"platform": self.platform, "auth_status": "connected",
                "note": "Token-based connection (Facebook Graph API page token)."}

    async def sync(self, workspace_id: str, conn: dict) -> dict:
        creds = await resolve_creds(self.platform, workspace_id)
        listings = await asyncio.to_thread(self._fetch_listings, creds)
        items = await db.items.find({"workspace_id": workspace_id}, {"_id": 0}).to_list(SYNC_MAX_ITEMS)
        price_by_item = {}
        for l in await db.listings.find({"workspace_id": workspace_id}, {"_id": 0}).to_list(SYNC_MAX_ITEMS):
            if l.get("item_id") and l["item_id"] not in price_by_item:
                price_by_item[l["item_id"]] = l.get("suggested_price")

        queued = 0
        for fb in listings:
            name = str(fb.get("name") or "").strip()
            try:
                anchor = float(fb.get("price") or 0)
            except (TypeError, ValueError):
                continue
            if not name or anchor <= 0:
                continue
            for it in items:
                if not (name.lower() in it["name"].lower() or it["name"].lower() in name.lower()):
                    continue
                current = price_by_item.get(it["id"])
                if current is None or anchor >= current * 0.95:
                    continue
                await db.suggestions.insert_one(Suggestion(
                    workspace_id=workspace_id, item_id=it["id"], item_name=it["name"],
                    type="reduce_price", title=f"Match Facebook Marketplace price",
                    detail=f"Facebook anchor is {anchor:.2f} vs your {current:.2f}.",
                    confidence=60, expected_impact="Faster sale", expected_outcome="Price competitive with Marketplace",
                    risk_level="medium", reason="External marketplace anchor is meaningfully lower",
                    params={"new_price": round(anchor, 2), "source": "facebook"},
                ).model_dump())
                queued += 1
        now = datetime.now(timezone.utc).isoformat()
        await db.integrations.update_one({"platform": self.platform, "workspace_id": workspace_id}, {"$set": {"last_sync": now}})
        await log_event(workspace_id, EventType.CONNECTOR_SYNC_EXECUTED, f"Sync executed for {self.platform}", {"platform": self.platform})
        await log_event(workspace_id, EventType.SYNC_ACTION_QUEUED, f"{self.platform} sync queued {queued} approval-gated action(s)", {"platform": self.platform, "queued": queued})
        return {"platform": self.platform, "last_sync": now, "listings_seen": len(listings),
                "suggestions_queued": queued, "note": "Approval-gated: nothing is posted or changed automatically."}
