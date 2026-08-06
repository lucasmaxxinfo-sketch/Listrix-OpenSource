"""Real Gmail connector (Gmail API, access token).

Communication adapter: sync() pulls recent buyer messages into the operations inbox
(never sends). connect() stores the token encrypted at rest. Outbound replies are
drafts stored on the inbox message — sending stays a manual, user-controlled step.
"""
import asyncio
import base64
import logging
import uuid
from datetime import datetime, timezone

import config
import requests
from deps import db
from services.events import EventType, log_event
from services.integrations.base import ConnectorAdapter, EncryptedTokenMixin
from services.integrations.creds import creds_configured, resolve_creds

logger = logging.getLogger(__name__)

GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"
SYNC_MAX_MESSAGES = 20


def _b64url_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


class GmailAdapter(EncryptedTokenMixin, ConnectorAdapter):
    platform = "Gmail"
    simulated = False

    def is_configured(self) -> bool:
        return bool(config.GMAIL_ACCESS_TOKEN)

    def _headers(self, creds=None):
        creds = creds or {}
        return {"Authorization": f"Bearer {creds.get('access_token') or config.GMAIL_ACCESS_TOKEN}"}

    # ---- network helpers (patchable in tests) ------------------------------------
    def _fetch_message_ids(self, creds=None):
        r = requests.get(f"{GMAIL_API}/messages", headers=self._headers(creds), params={"maxResults": SYNC_MAX_MESSAGES}, timeout=15)
        r.raise_for_status()
        return [m["id"] for m in r.json().get("messages", [])]

    def _fetch_message(self, creds, msg_id):
        r = requests.get(f"{GMAIL_API}/messages/{msg_id}", headers=self._headers(creds),
                         params={"format": "metadata", "metadataHeaders": "From,Subject"}, timeout=15)
        r.raise_for_status()
        return r.json()

    # ---- live connection test (used by the Connection Wizard) -----------------------
    async def test(self, workspace_id: str, conn: dict = None) -> dict:
        creds = await resolve_creds(self.platform, workspace_id)
        if not creds_configured(creds, self.platform):
            return {"ok": False, "message": "Missing Gmail access token. Add it in the wizard first."}
        try:
            r = await asyncio.to_thread(
                lambda: requests.get(f"{GMAIL_API}/profile", headers=self._headers(creds), timeout=15))
            r.raise_for_status()
            return {"ok": True, "message": "Gmail accepted your access token."}
        except Exception as e:
            logger.warning(f"Gmail connection test failed: {e}")
            return {"ok": False, "message": f"Gmail rejected the token: {e}"}

    # ---- adapter interface -------------------------------------------------------
    async def connect(self, workspace_id: str, conn: dict) -> dict:
        creds = await resolve_creds(self.platform, workspace_id)
        await db.integrations.update_one(
            {"platform": self.platform, "workspace_id": workspace_id},
            {"$set": {"auth_status": "connected", "sync_enabled": True,
                      "tokens": self._encrypt({"token": creds.get("access_token") or config.GMAIL_ACCESS_TOKEN})}},
        )
        await log_event(workspace_id, EventType.CONNECTOR_AUTH_SUCCESS, f"Connected to {self.platform}", {"platform": self.platform})
        return {"platform": self.platform, "auth_status": "connected",
                "note": "Token-based connection (Gmail API access token)."}

    async def sync(self, workspace_id: str, conn: dict) -> dict:
        creds = await resolve_creds(self.platform, workspace_id)
        ids = await asyncio.to_thread(self._fetch_message_ids, creds)
        items = await db.items.find({"workspace_id": workspace_id}, {"_id": 0}).to_list(200)
        imported = 0
        for msg_id in ids:
            try:
                msg = await asyncio.to_thread(self._fetch_message, creds, msg_id)
            except Exception as e:
                logger.warning(f"gmail message fetch failed ({msg_id}): {e}")
                continue
            headers = {h.get("name", ""): h.get("value", "") for h in (msg.get("payload") or {}).get("headers", [])}
            subject = headers.get("Subject") or "New buyer message"
            from_ = headers.get("From") or ""
            body = msg.get("snippet") or ""
            haystack = f"{subject} {body}".lower()
            linked = next((it for it in items if it["name"].lower() in haystack), None)
            await db.inbox.insert_one({
                "id": str(uuid.uuid4()), "workspace_id": workspace_id, "type": "BUYER_MESSAGE",
                "priority": "medium", "title": subject, "body": body, "from": from_,
                "source": "gmail", "simulated": False, "read": False, "reply_draft": None,
                "related_item_id": linked["id"] if linked else None,
                "related_item_name": linked["name"] if linked else None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            await log_event(workspace_id, EventType.INBOX_MESSAGE_RECEIVED, f"Inbox (Gmail): {subject}", {"from": from_})
            imported += 1
        now = datetime.now(timezone.utc).isoformat()
        await db.integrations.update_one({"platform": self.platform, "workspace_id": workspace_id}, {"$set": {"last_sync": now}})
        await log_event(workspace_id, EventType.CONNECTOR_SYNC_EXECUTED, f"Sync executed for {self.platform}", {"platform": self.platform, "imported": imported})
        return {"platform": self.platform, "last_sync": now, "messages_imported": imported,
                "note": "Read-only import; replies are drafts and sending stays manual."}
