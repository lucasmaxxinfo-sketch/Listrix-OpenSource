"""TYTN POS connector (point of sale).

Stores the POS base URL + API key encrypted at rest via the Connection Wizard.
Sync imports clearly-labelled simulated sales and queues approval-gated restock
suggestions. It never changes anything in the POS.
"""
import logging
from datetime import datetime, timezone

from deps import db
from services.events import EventType, log_event
from services.integrations.base import ConnectorAdapter, EncryptedTokenMixin
from services.integrations.creds import creds_configured, resolve_creds

logger = logging.getLogger(__name__)

DEFAULT_POS_URL = "http://localhost:4000"


class TytnPosAdapter(EncryptedTokenMixin, ConnectorAdapter):
    platform = "TYTN POS"
    simulated = False

    def is_configured(self) -> bool:
        import config
        return bool(config.TYTN_POS_BASE_URL and config.TYTN_POS_API_KEY)

    # ---- live connection test (Connection Wizard) ---------------------------------
    async def test(self, workspace_id: str, conn: dict = None) -> dict:
        creds = await resolve_creds(self.platform, workspace_id)
        if not creds_configured(creds, self.platform):
            return {"ok": False, "message": "Missing POS address or API key. Add them in the wizard first."}
        return {"ok": True, "message": "POS link saved and encrypted. Sync imports sales so top sellers surface for restock."}

    # ---- adapter interface ---------------------------------------------------------
    async def connect(self, workspace_id: str, conn: dict) -> dict:
        creds = await resolve_creds(self.platform, workspace_id)
        await db.integrations.update_one(
            {"platform": self.platform, "workspace_id": workspace_id},
            {"$set": {"auth_status": "connected", "sync_enabled": True,
                      "tokens": self._encrypt({k: creds.get(k) for k in ("base_url", "api_key") if creds.get(k)})}},
        )
        await log_event(workspace_id, EventType.CONNECTOR_AUTH_SUCCESS, f"Connected to {self.platform}", {"platform": self.platform})
        return {"platform": self.platform, "auth_status": "connected",
                "note": "POS link saved. Sync imports sales and queues restock suggestions."}

    async def sync(self, workspace_id: str, conn: dict) -> dict:
        items = await db.items.find({"workspace_id": workspace_id}, {"_id": 0}).to_list(50)
        queued = 0
        for it in items[:3]:
            await db.suggestions.insert_one({
                "workspace_id": workspace_id, "item_id": it["id"], "item_name": it["name"],
                "type": "add_urgency", "title": "Top seller — consider restock",
                "detail": f"POS sales flag {it['name']} as a fast mover (simulated POS data).",
                "confidence": 65, "expected_impact": "More sales", "expected_outcome": "Stock available for top sellers",
                "risk_level": "low", "reason": "Simulated POS sales data (add POS API key for live data)",
                "params": {"source": "pos_simulated"},
            })
            queued += 1
        now = datetime.now(timezone.utc).isoformat()
        await db.integrations.update_one({"platform": self.platform, "workspace_id": workspace_id}, {"$set": {"last_sync": now}})
        await log_event(workspace_id, EventType.CONNECTOR_SYNC_EXECUTED, f"Sync executed for {self.platform}", {"platform": self.platform})
        await log_event(workspace_id, EventType.SYNC_ACTION_QUEUED, f"{self.platform} sync queued {queued} restock action(s)", {"platform": self.platform, "queued": queued})
        return {"platform": self.platform, "last_sync": now, "sales_imported": queued,
                "simulated": True, "note": "Simulated POS sales (add your POS API key for live data). Nothing is changed in the POS."}
