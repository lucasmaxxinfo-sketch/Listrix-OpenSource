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
    "Stocksix": {
        "base_url": "Stocksix address (URL, e.g. http://localhost:3000)",
        "api_key": "API Key (Stocksix → Settings → Integrations)",
    },
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
    "eBay": {
        "client_id": "eBay App ID (Client ID)",
        "client_secret": "Client Secret",
        "refresh_token": "Refresh Token (optional)",
    },
    "govcr.online": {
        "email": "govcr.online email",
        "password": "govcr.online password",
    },
    "TYTN POS": {
        "base_url": "POS address (URL)",
        "api_key": "API Key",
    },
}

def _env_creds(platform: str) -> dict:
    """Environment-variable credentials, read live so tests/monkeypatches stay accurate."""
    if platform == "Stocksix":
        return {"base_url": config.STOCKSIX_BASE_URL, "api_key": config.STOCKSIX_API_KEY}
    if platform == "TradeMe":
        return {"consumer_key": config.TRADEME_CONSUMER_KEY,
                "consumer_secret": config.TRADEME_CONSUMER_SECRET,
                "callback_url": config.TRADEME_CALLBACK_URL}
    if platform == "Facebook Marketplace":
        return {"page_token": config.FACEBOOK_PAGE_TOKEN, "page_id": config.FACEBOOK_PAGE_ID}
    if platform == "Gmail":
        return {"access_token": config.GMAIL_ACCESS_TOKEN}
    if platform == "eBay":
        return {"client_id": config.EBAY_CLIENT_ID, "client_secret": config.EBAY_CLIENT_SECRET,
                "refresh_token": config.EBAY_REFRESH_TOKEN}
    if platform == "govcr.online":
        return {"email": config.GOVCR_EMAIL, "password": config.GOVCR_PASSWORD}
    if platform == "TYTN POS":
        return {"base_url": config.TYTN_POS_BASE_URL, "api_key": config.TYTN_POS_API_KEY}
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
