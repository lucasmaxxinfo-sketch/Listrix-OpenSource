"""Shared FastAPI dependencies and the async MongoDB handle."""
import logging
import os
from typing import Optional

from fastapi import Depends, Header, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

import config
from services.auth import decode_token
from services.ratelimit import llm_limiter
from utils import parse_iso

logger = logging.getLogger(__name__)


def create_mongo_client(mongo_url: str):
    """Build the Mongo client. `mongomock://` selects the in-memory client used by local tests."""
    if mongo_url.startswith("mongomock://"):
        from mongomock_motor import AsyncMongoMockClient

        return AsyncMongoMockClient()
    return AsyncIOMotorClient(mongo_url)


def _env_or_fallback(name: str, fallback: str) -> str:
    """Return the env var when set to a real value; fall back (dev) for missing/placeholder values."""
    value = os.environ.get(name, "").strip()
    if value and "<" not in value and "SET_YOUR" not in value:
        return value
    logger.warning("%s is missing or a placeholder — using %r (dev fallback).", name, fallback)
    return fallback


client = create_mongo_client(_env_or_fallback("MONGO_URL", "mongomock://"))
db = client[_env_or_fallback("DB_NAME", "listrix")]


async def get_optional_user(authorization: Optional[str] = Header(None)):
    """Return the authenticated user doc or None.

    No Authorization header -> None (pre-auth/legacy mode).
    A header with an invalid/expired token -> 401 so client bugs are not masked.
    """
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if isinstance(user.get("created_at"), str):
        user["created_at"] = parse_iso(user["created_at"])
    return user


async def get_current_user(user: Optional[dict] = Depends(get_optional_user)):
    """Return the authenticated user; require one only when AUTH_REQUIRED is on."""
    if config.AUTH_REQUIRED and user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def get_wid(x_workspace_id: Optional[str] = Header(None), user: Optional[dict] = Depends(get_current_user)):
    if config.AUTH_REQUIRED and user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    if x_workspace_id:
        ws = await db.workspaces.find_one({"id": x_workspace_id}, {"_id": 0, "id": 1, "owner_id": 1})
        if ws:
            if user is not None:
                owner = ws.get("owner_id")
                if owner and owner != user["id"]:
                    raise HTTPException(status_code=403, detail="Workspace does not belong to the authenticated user")
                if not owner and config.AUTH_REQUIRED:
                    raise HTTPException(status_code=403, detail="Workspace has no owner; claim it before access")
            return x_workspace_id
    # No/unknown header: fall back to the user's default workspace, else the global default.
    if user is not None:
        owned = await db.workspaces.find_one({"owner_id": user["id"], "is_default": True}, {"_id": 0, "id": 1})
        if not owned:
            owned = await db.workspaces.find_one({"owner_id": user["id"]}, {"_id": 0, "id": 1})
        if owned:
            return owned["id"]
        if config.AUTH_REQUIRED:
            raise HTTPException(status_code=403, detail="No workspace owned by the authenticated user")
    # lazy import avoids a circular dependency (deps -> migrations -> deps)
    from db.migrations import ensure_default_workspace

    ws = await ensure_default_workspace()
    return ws["id"]


async def rate_limit_llm(wid: str = Depends(get_wid)):
    if not llm_limiter.allow(wid):
        raise HTTPException(status_code=429, detail="Rate limit exceeded; try again shortly")
    return None
