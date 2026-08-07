"""Central configuration and constants for the Listrix backend."""
import logging
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# LLM provider — 100% open source by default. Listrix points at a LOCAL Ollama server
# (https://github.com/ollama/ollama) via its OpenAI-compatible endpoint, so no API key and no
# paid service are ever required. LLM_API_KEY is optional (local servers accept any dummy key);
# override LLM_BASE_URL/LLM_MODEL only if you deliberately point at another endpoint.
def _env_str(name: str, default: str) -> str:
    """Env value or default — treats empty/whitespace as unset so a blank .env line can never
    silently disable the local open-source defaults (e.g. by pointing at a paid endpoint)."""
    value = os.environ.get(name, "").strip()
    return value if value else default


LLM_MODEL = _env_str("LLM_MODEL", "llama3.2-vision")
LLM_API_KEY = _env_str("LLM_API_KEY", "")
LLM_BASE_URL = _env_str("LLM_BASE_URL", "http://localhost:11434/v1")

# LLM resilience (see services/llm.py)
LLM_MAX_RETRIES = int(os.environ.get("LLM_MAX_RETRIES", "3"))
LLM_RETRY_BASE_DELAY = float(os.environ.get("LLM_RETRY_BASE_DELAY", "1.0"))
LLM_CACHE_TTL = int(os.environ.get("LLM_CACHE_TTL", "600"))
LLM_CACHE_MAX_ENTRIES = int(os.environ.get("LLM_CACHE_MAX_ENTRIES", "256"))

# Authentication (HANDOVER §25). AUTH_REQUIRED=false keeps the pre-auth single-operator
# behavior (silent fallback) while auth endpoints/ownership are fully functional;
# set AUTH_REQUIRED=true to lock every /api route behind a JWT.
AUTH_REQUIRED = os.environ.get("AUTH_REQUIRED", "false").lower() in ("1", "true", "yes")
JWT_ALGORITHM = "HS256"
JWT_SECRET = os.environ.get("JWT_SECRET", "")
JWT_TTL_SECONDS = int(os.environ.get("JWT_TTL_SECONDS", "86400"))


def _load_jwt_secret() -> str:
    """Return the env secret, or a persistent dev secret so tokens survive restarts.

    Production must set JWT_SECRET (env takes precedence). Without it, a secret is
    generated once and stored in a gitignored local file, so auth tokens no longer
    invalidate every time the backend restarts.
    """
    if JWT_SECRET.strip():
        return JWT_SECRET.strip()
    path = ROOT_DIR / ".jwt_secret"
    try:
        if path.exists():
            stored = path.read_text(encoding="utf-8").strip()
            if stored:
                return stored
    except OSError:
        pass
    generated = secrets.token_urlsafe(48)
    try:
        path.write_text(generated, encoding="utf-8")
        os.chmod(path, 0o600)
    except OSError:
        logger.warning("JWT_SECRET is not set and could not persist a dev secret - tokens invalidate on restart")
    else:
        logger.warning("JWT_SECRET is not set - generated a persistent dev secret at %s", path)
    return generated


JWT_SECRET = _load_jwt_secret()

# Per-workspace rate limit for LLM endpoints (in-process sliding window).
LLM_RATE_LIMIT_PER_MINUTE = int(os.environ.get("LLM_RATE_LIMIT_PER_MINUTE", "30"))
LLM_RATE_WINDOW_SECONDS = int(os.environ.get("LLM_RATE_WINDOW_SECONDS", "60"))

# Real TradeMe connector (services/integrations/trademe.py). When the consumer key/secret
# are set, TradeMe connect/sync use OAuth 1.0a against the live API; otherwise the legacy
# simulated toggle is preserved (preview + isolation suite).
TRADEME_CONSUMER_KEY = os.environ.get("TRADEME_CONSUMER_KEY", "")
TRADEME_CONSUMER_SECRET = os.environ.get("TRADEME_CONSUMER_SECRET", "")
TRADEME_CALLBACK_URL = os.environ.get("TRADEME_CALLBACK_URL", "")
# Fernet key (32-byte urlsafe-base64) for encrypting connector tokens at rest.
# Falls back to a key derived from JWT_SECRET (dev only; tokens unreadable after restart).
CONNECTOR_ENCRYPTION_KEY = os.environ.get("CONNECTOR_ENCRYPTION_KEY", "")

# Real Facebook Marketplace connector (services/integrations/facebook.py). Token-based:
# set FACEBOOK_PAGE_TOKEN (+ optional FACEBOOK_PAGE_ID) to enable live sync.
FACEBOOK_PAGE_TOKEN = os.environ.get("FACEBOOK_PAGE_TOKEN", "")
FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID", "")

# Real Gmail connector (services/integrations/gmail.py). Token-based: set
# GMAIL_ACCESS_TOKEN to pull buyer messages into the inbox (read-only).
GMAIL_ACCESS_TOKEN = os.environ.get("GMAIL_ACCESS_TOKEN", "")

# Real Stocksix connector (services/integrations/stocksix.py). The owner's Stocksix
# hub is a local-first open-source inventory app with a public bearer-key API:
#   GET {STOCKSIX_BASE_URL}/api/public/v1/inventory
# Wizard credentials (base_url + api_key) override these env fallbacks.
STOCKSIX_BASE_URL = os.environ.get("STOCKSIX_BASE_URL", "")
STOCKSIX_API_KEY = os.environ.get("STOCKSIX_API_KEY", "")

# Financials reporting (services/financials.py): default marketplace fee rate as a fraction.
MARKETPLACE_FEE_RATE = float(os.environ.get("MARKETPLACE_FEE_RATE", "0.079"))

# Optional background scheduler (services/scheduler.py): OFF by default so tests and local
# dev stay deterministic; enable with SCHEDULER_ENABLED=true in production.
SCHEDULER_ENABLED = os.environ.get("SCHEDULER_ENABLED", "false").lower() in ("1", "true", "yes")
SCHEDULER_INTERVAL_MINUTES = int(os.environ.get("SCHEDULER_INTERVAL_MINUTES", "60"))

SUGGESTION_TYPES = {"reduce_price", "improve_title", "add_keywords", "relist", "add_urgency", "generate_listing"}
CLIENT_EVENT_TYPES = {"WIDGET_VIEWED", "VOICE_QUERY_RECEIVED", "USER_APPROVED_ACTION", "COMMAND_CENTER_OPENED"}
# collections that are workspace-scoped (used by the legacy migration)
SCOPED = ["items", "listings", "events", "performance", "suggestions", "price_history", "briefs", "feedback", "integrations", "inbox"]

DEFAULT_CONNECTORS = [
    {"platform": "Stocksix", "kind": "inventory", "auth_status": "disconnected", "permissions": ["read_inventory", "sync_items"], "sync_enabled": False},
    {"platform": "TradeMe", "kind": "marketplace", "auth_status": "disconnected", "permissions": ["read_listings", "create_listing_draft"], "sync_enabled": False},
    {"platform": "Facebook Marketplace", "kind": "marketplace", "auth_status": "disconnected", "permissions": ["read_listings"], "sync_enabled": False},
    {"platform": "Gmail", "kind": "communication", "auth_status": "disconnected", "permissions": ["read_messages"], "sync_enabled": False},
    {"platform": "Pricing Signals", "kind": "data", "auth_status": "disconnected", "permissions": ["read_market_prices"], "sync_enabled": False},
    {"platform": "Competitor Listings", "kind": "data", "auth_status": "disconnected", "permissions": ["read_competitors"], "sync_enabled": False},
]
