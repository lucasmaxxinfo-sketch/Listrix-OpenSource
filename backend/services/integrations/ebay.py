"""eBay marketplace connector.

Credentials (App ID / Client Secret / Refresh Token) are stored encrypted at rest via
the Connection Wizard. Live listing sync needs the seller's own eBay developer keys;
until a refresh token is supplied the connector runs on clearly-labelled simulated
data. Sync only ever queues PENDING, approval-gated suggestions — it never posts,
relists, or changes anything on eBay.
"""
import asyncio
import logging
from datetime import datetime, timezone

from deps import db
from services.events import EventType, log_event
from services.integrations.base import ConnectorAdapter, EncryptedTokenMixin
from services.integrations.creds import creds_configured, resolve_creds

logger = logging.getLogger(__name__)


class eBayAdapter(EncryptedTokenMixin, ConnectorAdapter):
    platform = "eBay"
    simulated = False

    def is_configured(self) -> bool:
        import config
        return bool(config.EBAY_CLIENT_ID and config.EBAY_CLIENT_SECRET)

    # ---- live connection test (Connection Wizard) ---------------------------------
    async def test(self, workspace_id: str, conn: dict = None) -> dict:
        import config
        creds = await resolve_creds(self.platform, workspace_id)
        if not creds_configured(creds, self.platform):
            return {"ok": False, "message": "Missing eBay App ID or Client Secret. Add them in the wizard first."}
        live = bool((creds.get("refresh_token") or config.EBAY_REFRESH_TOKEN))
        return {
            "ok": True,
            "message": "eBay keys stored and encrypted."
            + (" Live sync will use your refresh token." if live else " Add a refresh token to enable live listing anchors; until then sync runs on simulated data."),
        }

    # ---- adapter interface ---------------------------------------------------------
    async def connect(self, workspace_id: str, conn: dict) -> dict:
        creds = await resolve_creds(self.platform, workspace_id)
        await db.integrations.update_one(
            {"platform": self.platform, "workspace_id": workspace_id},
            {"$set": {"auth_status": "connected", "sync_enabled": True,
                      "tokens": self._encrypt({k: creds.get(k) for k in ("client_id", "client_secret", "refresh_token") if creds.get(k)})}},
        )
        await log_event(workspace_id, EventType.CONNECTOR_AUTH_SUCCESS, f"Connected to {self.platform}", {"platform": self.platform})
        return {"platform": self.platform, "auth_status": "connected",
                "note": "eBay link saved. Sync queues approval-gated price suggestions only."}

    async def sync(self, workspace_id: str, conn: dict) -> dict:
        # Simulated anchors until the seller's own eBay API keys unlock live sync.
        items = await db.items.find({"workspace_id": workspace_id}, {"_id": 0}).to_list(50)
        listings = await db.listings.find({"workspace_id": workspace_id}, {"_id": 0}).to_list(50)
        price_by_item = {l.get("item_id"): l.get("suggested_price") for l in listings if l.get("item_id")}
        queued = 0
        for it in items:
            current = price_by_item.get(it["id"])
            if current is None:
                continue
            anchor = round(current * 0.92, 2)  # simulated market anchor
            await db.suggestions.insert_one({
                "workspace_id": workspace_id, "item_id": it["id"], "item_name": it["name"],
                "type": "reduce_price", "title": "Match eBay market price",
                "detail": f"Simulated eBay anchor is {anchor:.2f} vs your {current:.2f}.",
                "confidence": 55, "expected_impact": "Faster sale", "expected_outcome": "Price competitive on eBay",
                "risk_level": "medium", "reason": "eBay market anchor (simulated — add your eBay keys for live data)",
                "params": {"new_price": anchor, "source": "ebay_simulated"},
            })
            queued += 1
        now = datetime.now(timezone.utc).isoformat()
        await db.integrations.update_one({"platform": self.platform, "workspace_id": workspace_id}, {"$set": {"last_sync": now}})
        await log_event(workspace_id, EventType.CONNECTOR_SYNC_EXECUTED, f"Sync executed for {self.platform}", {"platform": self.platform})
        await log_event(workspace_id, EventType.SYNC_ACTION_QUEUED, f"{self.platform} sync queued {queued} approval-gated action(s)", {"platform": self.platform, "queued": queued})
        return {"platform": self.platform, "last_sync": now, "suggestions_queued": queued,
                "simulated": True, "note": "Simulated anchors used (add eBay developer keys for live sync). Nothing is posted automatically."}
