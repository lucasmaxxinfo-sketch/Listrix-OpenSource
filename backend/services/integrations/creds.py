"""Credential resolution for live connectors.

The Connection Wizard saves credentials encrypted per workspace (integrations.setup);
those take priority. Server environment variables remain the fallback, so staging via
env vars (and the existing test suite) keeps working unchanged.
"""
import logging

import config

logger = logging.getLogger(__name__)

# Field labels shown in the Connection Wizard, per platform.
PLATFORM_CRED_FIELDS = {
    "TradeMe": {
        "consumer_key": "Consumer Key",
        "consumer_secret": "Consumer Secret",
        "callback_url": "Callback URL (optional)",
    },
    "Facebook Marketplace": {
        "page_token": "Page Access Token",
        "page_id": "Page ID (optional)",
    },
    "Gmail": {
        "access_token": "Gmail Access Token",
    },
}

def _env_creds(platform: str) -> dict:
    """Environment-variable credentials, read live so tests/monkeypatches stay accurate."""
    if platform == "TradeMe":
        return {"consumer_key": config.TRADEME_CONSUMER_KEY,
                "consumer_secret": config.TRADEME_CONSUMER_SECRET,
                "callback_url": config.TRADEME_CALLBACK_URL}
    if platform == "Facebook Marketplace":
        return {"page_token": config.FACEBOOK_PAGE_TOKEN, "page_id": config.FACEBOOK_PAGE_ID}
    if platform == "Gmail":
        return {"access_token": config.GMAIL_ACCESS_TOKEN}
    return {}


def required_fields(platform: str) -> list:
    """Keys that must have a value for the connection to go live."""
    return [k for k, label in PLATFORM_CRED_FIELDS.get(platform, {}).items() if "(optional)" not in label]


def creds_configured(creds: dict, platform: str) -> bool:
    return all(bool((creds or {}).get(k)) for k in required_fields(platform))


async def resolve_creds(platform: str, wid: str) -> dict:
    """Stored wizard credentials override environment variables."""
    stored = {}
    try:
        from deps import db

        doc = await db.integrations.find_one({"platform": platform, "workspace_id": wid}, {"_id": 0, "setup": 1})
        if doc and doc.get("setup"):
            from services.integrations import get_adapter

            adapter = get_adapter(platform)
            if adapter is not None:
                stored = adapter._decrypt(doc["setup"]) or {}
    except Exception as e:  # pragma: no cover - defensive
        logger.warning(f"Failed to resolve stored credentials for {platform}: {e}")
    return {**_env_creds(platform), **stored}
