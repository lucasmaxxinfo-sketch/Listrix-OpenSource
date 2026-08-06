"""Real TradeMe connector (OAuth 1.0a).

- connect(): starts the 3-legged OAuth flow and returns the authorize URL.
- complete_oauth(): exchanges the verifier for an access token, stored ENCRYPTED at rest.
- sync(): fetches the seller's current TradeMe listings + market anchors and creates
  PENDING (approval-gated) suggestions only. Never posts or mutates listings.

Network calls run via asyncio.to_thread so the event loop never blocks.
"""
import asyncio
import base64
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import config
from deps import db
from models import Suggestion
from services.events import EventType, log_event
from services.integrations.base import ConnectorAdapter
from services.integrations.creds import creds_configured, resolve_creds

logger = logging.getLogger(__name__)

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover
    Fernet = None
    InvalidToken = Exception

try:
    from requests_oauthlib import OAuth1Session
except ImportError:  # pragma: no cover
    OAuth1Session = None

TRADEME_API = "https://api.trademe.co.nz"
REQUEST_TOKEN_URL = f"{TRADEME_API}/v1/OAuth/RequestToken"
AUTHORIZE_URL = f"{TRADEME_API}/v1/OAuth/Authorize"
ACCESS_TOKEN_URL = f"{TRADEME_API}/v1/OAuth/AccessToken"
SELLING_URL = f"{TRADEME_API}/v1/MyTradeMe/Selling"
SEARCH_URL = f"{TRADEME_API}/v1/Search/General"
SYNC_MAX_ITEMS = 100


def _derived_encryption_key() -> bytes:
    material = (config.JWT_SECRET or "listrix-dev-secret").encode("utf-8")
    return base64.urlsafe_b64encode(hashlib.sha256(material).digest())


class TradeMeAdapter(ConnectorAdapter):
    platform = "TradeMe"
    simulated = False

    def is_configured(self) -> bool:
        return bool(config.TRADEME_CONSUMER_KEY and config.TRADEME_CONSUMER_SECRET)

    # ---- token encryption at rest -------------------------------------------------
    def _fernet(self):
        key = config.CONNECTOR_ENCRYPTION_KEY or _derived_encryption_key().decode("ascii")
        if Fernet is None:
            raise RuntimeError("cryptography package is not installed")
        return Fernet(key.encode("ascii"))

    def _encrypt(self, payload: dict) -> str:
        return self._fernet().encrypt(json.dumps(payload).encode("utf-8")).decode("ascii")

    def _decrypt(self, blob: str) -> dict:
        try:
            return json.loads(self._fernet().decrypt(blob.encode("ascii")))
        except (InvalidToken, ValueError) as e:
            logger.error(f"Failed to decrypt connector tokens: {e}")
            raise RuntimeError("Stored connector tokens are unreadable (encryption key changed?)")

    # ---- network helpers (patchable in tests) -------------------------------------
    def _oauth_session(self, creds=None, resource_owner_key=None, resource_owner_secret=None, verifier=None):
        creds = creds or {}
        return OAuth1Session(
            creds.get("consumer_key") or config.TRADEME_CONSUMER_KEY,
            client_secret=creds.get("consumer_secret") or config.TRADEME_CONSUMER_SECRET,
            resource_owner_key=resource_owner_key,
            resource_owner_secret=resource_owner_secret,
            verifier=verifier,
        )

    def _public_session(self, creds=None):
        """Key-only OAuth session for TradeMe public search endpoints."""
        creds = creds or {}
        return OAuth1Session(creds.get("consumer_key") or config.TRADEME_CONSUMER_KEY)

    async def _fetch_request_token_pair(self, creds=None) -> (str, str):
        session = self._oauth_session(creds)
        token = await asyncio.to_thread(session.fetch_request_token, REQUEST_TOKEN_URL)
        return token["oauth_token"], token["oauth_token_secret"]

    async def _fetch_access_token_pair(self, creds, oauth_token, oauth_token_secret, oauth_verifier) -> (str, str):
        session = self._oauth_session(
            creds,
            resource_owner_key=oauth_token,
            resource_owner_secret=oauth_token_secret,
            verifier=oauth_verifier,
        )
        access = await asyncio.to_thread(session.fetch_access_token, ACCESS_TOKEN_URL)
        return access["oauth_token"], access["oauth_token_secret"]

    async def _fetch_selling_listings(self, session) -> List[dict]:
        resp = await asyncio.to_thread(session.get, SELLING_URL, params={"rows": 50})
        resp.raise_for_status()
        return resp.json().get("List", []) or []

    async def _search_median_price(self, session, query: str) -> Optional[float]:
        resp = await asyncio.to_thread(session.get, SEARCH_URL, params={"q": query, "rows": 6})
        resp.raise_for_status()
        prices = []
        for row in resp.json().get("List", []) or []:
            p = row.get("StartPrice") or row.get("AsAtPrice") or row.get("BuyNowPrice")
            if p:
                try:
                    prices.append(float(p))
                except (TypeError, ValueError):
                    continue
        prices = sorted(p for p in prices if p > 0)
        return prices[len(prices) // 2] if prices else None

    # ---- live connection test (used by the Connection Wizard) -----------------------
    async def test(self, workspace_id: str, conn: Dict[str, Any] = None) -> Dict[str, Any]:
        creds = await resolve_creds(self.platform, workspace_id)
        if not creds_configured(creds, self.platform):
            return {"ok": False, "message": "Missing TradeMe consumer key and secret. Add them in the wizard first."}
        if OAuth1Session is None:  # pragma: no cover
            return {"ok": False, "message": "requests_oauthlib is not installed on the server."}
        try:
            session = self._oauth_session(creds)
            token = await asyncio.to_thread(session.fetch_request_token, REQUEST_TOKEN_URL)
            if not token:
                raise RuntimeError("empty request token response")
            return {"ok": True, "message": "TradeMe accepted your consumer credentials. You can now start the authorization flow."}
        except Exception as e:
            logger.warning(f"TradeMe connection test failed: {e}")
            return {"ok": False, "message": f"TradeMe rejected the credentials: {e}"}

    # ---- flow ---------------------------------------------------------------------
    async def connect(self, workspace_id: str, conn: Dict[str, Any]) -> Dict[str, Any]:
        creds = await resolve_creds(self.platform, workspace_id)
        oauth_token, oauth_token_secret = await self._fetch_request_token_pair(creds)
        authorize_url = f"{AUTHORIZE_URL}?oauth_token={oauth_token}"
        callback = creds.get("callback_url") or config.TRADEME_CALLBACK_URL
        if callback:
            authorize_url += f"&callback={callback}"
        await db.integrations.update_one(
            {"platform": self.platform, "workspace_id": workspace_id},
            {"$set": {
                "config": self._encrypt({"oauth_token": oauth_token, "oauth_token_secret": oauth_token_secret}),
                "auth_status": "authorizing",
                "sync_enabled": False,
            }},
        )
        await log_event(workspace_id, EventType.CONNECTOR_AUTH_STARTED,
                        "TradeMe authorization started", {"platform": self.platform})
        return {
            "platform": self.platform,
            "status": "authorization_required",
            "auth_status": "authorizing",
            "authorize_url": authorize_url,
            "note": "Authorize in the browser, then the callback verifier completes the connection.",
        }

    async def complete_oauth(self, workspace_id: str, oauth_token: str, oauth_verifier: str,
                             conn: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        doc = conn or await db.integrations.find_one({"platform": self.platform, "workspace_id": workspace_id}, {"_id": 0})
        if not doc:
            raise LookupError("Connector not found")
        state = self._decrypt(doc.get("config") or "")
        if state.get("oauth_token") != oauth_token:
            raise LookupError("OAuth token mismatch - restart the connection flow")
        oauth_token_secret = state["oauth_token_secret"]
        creds = await resolve_creds(self.platform, workspace_id)
        access_token, access_token_secret = await self._fetch_access_token_pair(
            creds, oauth_token, oauth_token_secret, oauth_verifier
        )
        await db.integrations.update_one(
            {"platform": self.platform, "workspace_id": workspace_id},
            {"$set": {
                "tokens": self._encrypt({"oauth_token": access_token, "oauth_token_secret": access_token_secret}),
                "config": None,
                "auth_status": "connected",
                "sync_enabled": True,
            }},
        )
        await log_event(workspace_id, EventType.CONNECTOR_AUTH_SUCCESS,
                        f"Connected to {self.platform}", {"platform": self.platform})
        return {"platform": self.platform, "auth_status": "connected"}

    async def sync(self, workspace_id: str, conn: Dict[str, Any]) -> Dict[str, Any]:
        tokens = self._decrypt(conn.get("tokens") or "")
        creds = await resolve_creds(self.platform, workspace_id)
        session = self._oauth_session(
            creds,
            resource_owner_key=tokens["oauth_token"],
            resource_owner_secret=tokens["oauth_token_secret"],
        )
        sold = await self._fetch_selling_listings(session)
        remote = {}
        for l in sold:
            title = (l.get("Title") or "").strip().lower()
            if not title:
                continue
            p = l.get("StartPrice") or l.get("AsAtPrice") or l.get("BuyNowPrice")
            try:
                remote[title] = float(p) if p is not None else None
            except (TypeError, ValueError):
                remote[title] = None

        items = await db.items.find({"workspace_id": workspace_id}, {"_id": 0, "image": 0}).sort("created_at", -1).to_list(SYNC_MAX_ITEMS)
        public_session = self._public_session(creds)
        created = 0
        for it in items:
            listing = await db.listings.find_one(
                {"workspace_id": workspace_id, "$or": [{"item_id": it["id"]}, {"source_name": it["name"]}]},
                {"_id": 0}, sort=[("created_at", -1)],
            )
            if not listing:
                continue
            current = listing.get("suggested_price")
            if current is None:
                continue
            anchor = remote.get(it["name"].strip().lower())
            if anchor is None:
                anchor = await self._search_median_price(public_session, it["name"])
            if anchor is None or anchor <= 0 or anchor >= current * 0.95:
                continue
            await db.suggestions.delete_many({
                "workspace_id": workspace_id, "item_id": it["id"], "status": "pending", "type": "reduce_price",
            })
            sugg = Suggestion(
                workspace_id=workspace_id, item_id=it["id"], item_name=it["name"], listing_id=listing["id"],
                type="reduce_price",
                title=f"TradeMe market anchor: {it['name']}",
                detail=f"Live TradeMe comparables average ${anchor:.2f} vs current ${current:.2f}. Reduce to stay competitive.",
                confidence=75.0, expected_impact="Faster sale vs live TradeMe comparables",
                expected_outcome="Competitive price point on TradeMe", risk_level="medium",
                reason=f"TradeMe anchor ${anchor:.2f} is below current price ${current:.2f}",
                params={"new_price": round(anchor, 2)},
            )
            sdoc = sugg.model_dump()
            sdoc["created_at"] = sdoc["created_at"].isoformat()
            await db.suggestions.insert_one({**sdoc})
            created += 1

        now = datetime.now(timezone.utc).isoformat()
        await db.integrations.update_one({"platform": self.platform, "workspace_id": workspace_id}, {"$set": {"last_sync": now}})
        await log_event(workspace_id, EventType.CONNECTOR_SYNC_EXECUTED, f"Sync executed for {self.platform}", {"platform": self.platform})
        await log_event(workspace_id, EventType.EXTERNAL_DATA_RECEIVED,
                        "Live TradeMe market data received", {"platform": self.platform, "simulated": False})
        await log_event(workspace_id, EventType.SYNC_ACTION_QUEUED,
                        f"TradeMe sync queued {created} approval-gated action(s)", {"platform": self.platform, "count": created})
        return {
            "platform": self.platform,
            "last_sync": now,
            "simulated": False,
            "suggestions_created": created,
            "note": f"TradeMe sync complete: {created} pending suggestion(s) queued for approval. No listings were changed.",
        }
