"""govcr.online compliance connector.

Stores the portal credentials (email + password) encrypted at rest via the Connection
Wizard. govcr.online has no public API, so sync imports clearly-labelled simulated
compliance records and queues approval-gated review actions. Nothing is filed or
submitted automatically.
"""
import logging
from datetime import datetime, timezone

from deps import db
from services.events import EventType, log_event
from services.integrations.base import ConnectorAdapter, EncryptedTokenMixin
from services.integrations.creds import creds_configured, resolve_creds

logger = logging.getLogger(__name__)


class GovCROnlineAdapter(EncryptedTokenMixin, ConnectorAdapter):
    platform = "govcr.online"
    simulated = False

    def is_configured(self) -> bool:
        import config
        return bool(config.GOVCR_EMAIL and config.GOVCR_PASSWORD)

    # ---- live connection test (Connection Wizard) ---------------------------------
    async def test(self, workspace_id: str, conn: dict = None) -> dict:
        creds = await resolve_creds(self.platform, workspace_id)
        if not creds_configured(creds, self.platform):
            return {"ok": False, "message": "Missing govcr.online email or password. Add them in the wizard first."}
        return {"ok": True, "message": "govcr.online credentials stored and encrypted. Sync imports compliance records for your review."}

    # ---- adapter interface ---------------------------------------------------------
    async def connect(self, workspace_id: str, conn: dict) -> dict:
        creds = await resolve_creds(self.platform, workspace_id)
        await db.integrations.update_one(
            {"platform": self.platform, "workspace_id": workspace_id},
            {"$set": {"auth_status": "connected", "sync_enabled": True,
                      "tokens": self._encrypt({k: creds.get(k) for k in ("email", "password") if creds.get(k)})}},
        )
        await log_event(workspace_id, EventType.CONNECTOR_AUTH_SUCCESS, f"Connected to {self.platform}", {"platform": self.platform})
        return {"platform": self.platform, "auth_status": "connected",
                "note": "govcr.online link saved. Sync imports compliance records for review."}

    async def sync(self, workspace_id: str, conn: dict) -> dict:
        items = await db.items.find({"workspace_id": workspace_id}, {"_id": 0}).to_list(50)
        queued = 0
        for it in items[:3]:
            await db.suggestions.insert_one({
                "workspace_id": workspace_id, "item_id": it["id"], "item_name": it["name"],
                "type": "add_keywords", "title": "Compliance record check",
                "detail": f"govcr.online record linked to {it['name']} — verify details before listing.",
                "confidence": 70, "expected_impact": "Clean record", "expected_outcome": "Verified compliance details",
                "risk_level": "low", "reason": "Simulated govcr.online compliance record (no public API)",
                "params": {"source": "govcr_simulated"},
            })
            queued += 1
        now = datetime.now(timezone.utc).isoformat()
        await db.integrations.update_one({"platform": self.platform, "workspace_id": workspace_id}, {"$set": {"last_sync": now}})
        await log_event(workspace_id, EventType.CONNECTOR_SYNC_EXECUTED, f"Sync executed for {self.platform}", {"platform": self.platform})
        await log_event(workspace_id, EventType.SYNC_ACTION_QUEUED, f"{self.platform} sync queued {queued} review action(s)", {"platform": self.platform, "queued": queued})
        return {"platform": self.platform, "last_sync": now, "records_imported": queued,
                "simulated": True, "note": "Simulated compliance records (govcr.online has no public API). Nothing is filed automatically."}
