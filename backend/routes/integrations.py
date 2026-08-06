"""Integration connector routes.

Live connectors (TradeMe, Facebook Marketplace, Gmail) are driven by credentials that
come either from server environment variables or, with the Connection Wizard, from
encrypted per-workspace settings (integrations.setup). Platforms without a live adapter
keep the legacy simulated toggle. Secrets are never returned to the client.
"""
from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

import config
from deps import db, get_wid
from models import OAuthCallbackRequest
from services.events import EventType, log_event
from services.integrations import get_adapter
from services.integrations.creds import PLATFORM_CRED_FIELDS, creds_configured, resolve_creds

router = APIRouter()


class ConnectorConfigRequest(BaseModel):
    credentials: Dict[str, str] = {}


async def seed_connectors(wid):
    if await db.integrations.count_documents({"workspace_id": wid}) == 0:
        for c in config.DEFAULT_CONNECTORS:
            await db.integrations.insert_one({**c, "workspace_id": wid, "last_sync": None})


def _public_projection():
    # never expose encrypted tokens, OAuth state, or wizard secrets to the client
    return {"_id": 0, "tokens": 0, "config": 0, "setup": 0}


@router.get("/integrations")
async def list_integrations(wid: str = Depends(get_wid)):
    await seed_connectors(wid)
    return await db.integrations.find({"workspace_id": wid}, _public_projection()).to_list(50)


@router.get("/integrations/status")
async def integration_status(wid: str = Depends(get_wid)):
    """Per-connector wizard status: live vs simulated, what's missing, last test result."""
    await seed_connectors(wid)
    rows = await db.integrations.find({"workspace_id": wid}, {"_id": 0, "tokens": 0, "config": 0}).to_list(50)
    out = []
    for c in rows:
        platform = c["platform"]
        adapter = get_adapter(platform)
        stored = bool(c.pop("setup", None))
        creds = await resolve_creds(platform, wid) if adapter else {}
        configured = creds_configured(creds, platform) if adapter else False
        out.append({
            **c,
            "mode": "live" if configured else "simulated",
            "configured": configured,
            "credentials_stored": stored,
            "requires": list(PLATFORM_CRED_FIELDS.get(platform, {}).keys()),
        })
    return out


@router.post("/integrations/{platform}/config")
async def save_integration_config(platform: str, payload: ConnectorConfigRequest, wid: str = Depends(get_wid)):
    """Save live credentials for a platform, encrypted at rest (Connection Wizard step)."""
    await seed_connectors(wid)
    fields = PLATFORM_CRED_FIELDS.get(platform)
    if not fields:
        raise HTTPException(status_code=404, detail="This connector does not accept in-app credentials")
    adapter = get_adapter(platform)
    if not adapter:
        raise HTTPException(status_code=404, detail="This connector does not accept in-app credentials")
    cleaned = {k: str(v).strip() for k, v in (payload.credentials or {}).items() if k in fields and str(v).strip()}
    if not cleaned:
        raise HTTPException(status_code=400, detail="Provide at least one credential value")
    await db.integrations.update_one(
        {"platform": platform, "workspace_id": wid},
        {"$set": {"setup": adapter._encrypt(cleaned), "auth_status": "configured"}},
    )
    await log_event(wid, EventType.CONNECTOR_AUTH_SUCCESS,
                    f"Live credentials saved for {platform}", {"platform": platform, "fields": sorted(cleaned)})
    return {"platform": platform, "auth_status": "configured", "configured": creds_configured(cleaned, platform)}


@router.post("/integrations/{platform}/test")
async def test_integration(platform: str, wid: str = Depends(get_wid)):
    """Live connectivity test against the real provider (Connection Wizard step)."""
    await seed_connectors(wid)
    adapter = get_adapter(platform)
    if not adapter:
        raise HTTPException(status_code=404, detail="This connector does not support a live test")
    try:
        result = await adapter.test(wid)
    except Exception as e:
        result = {"ok": False, "message": f"Connection test failed: {e}"}
    result["at"] = datetime.now(timezone.utc).isoformat()
    await db.integrations.update_one(
        {"platform": platform, "workspace_id": wid},
        {"$set": {"last_test": {"ok": result["ok"], "message": result["message"], "at": result["at"]}}},
    )
    return result


@router.post("/integrations/{platform}/connect")
async def connect_integration(platform: str, wid: str = Depends(get_wid)):
    await seed_connectors(wid)
    conn = await db.integrations.find_one({"platform": platform, "workspace_id": wid}, {"_id": 0})
    if not conn:
        raise HTTPException(status_code=404, detail="Connector not found")
    adapter = get_adapter(platform)
    if adapter:
        creds = await resolve_creds(platform, wid)
        if creds_configured(creds, platform):
            # Real OAuth flow (TradeMe): returns the authorize URL; connection completes via callback.
            try:
                return await adapter.connect(wid, conn)
            except Exception as e:
                await log_event(wid, EventType.AI_ERROR, f"{platform} connect failed", {"error": str(e)})
                raise HTTPException(status_code=502, detail=f"{platform} connection failed: {e}")
    # Legacy simulated toggle (no live credentials configured).
    ns = "disconnected" if conn.get("auth_status") == "connected" else "connected"
    await db.integrations.update_one({"platform": platform, "workspace_id": wid}, {"$set": {"auth_status": ns, "sync_enabled": ns == "connected"}})
    if ns == "connected":
        await log_event(wid, EventType.CONNECTOR_AUTH_SUCCESS, f"Connected to {platform}", {"platform": platform})
    return {"platform": platform, "auth_status": ns}


@router.post("/integrations/{platform}/oauth/callback")
async def oauth_callback(platform: str, payload: OAuthCallbackRequest, wid: str = Depends(get_wid)):
    adapter = get_adapter(platform)
    if not adapter:
        raise HTTPException(status_code=404, detail="Platform does not support an OAuth callback")
    if not creds_configured(await resolve_creds(platform, wid), platform):
        raise HTTPException(status_code=404, detail="Platform does not support an OAuth callback")
    conn = await db.integrations.find_one({"platform": platform, "workspace_id": wid}, {"_id": 0})
    if not conn:
        raise HTTPException(status_code=404, detail="Connector not found")
    try:
        return await adapter.complete_oauth(wid, payload.oauth_token, payload.oauth_verifier, conn)
    except LookupError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await log_event(wid, EventType.AI_ERROR, f"{platform} OAuth callback failed", {"error": str(e)})
        raise HTTPException(status_code=502, detail=f"{platform} OAuth callback failed: {e}")


@router.post("/integrations/{platform}/sync")
async def sync_integration(platform: str, wid: str = Depends(get_wid)):
    conn = await db.integrations.find_one({"platform": platform, "workspace_id": wid}, {"_id": 0})
    if not conn:
        raise HTTPException(status_code=404, detail="Connector not found")
    if conn.get("auth_status") != "connected":
        raise HTTPException(status_code=400, detail="Connector is not connected")
    adapter = get_adapter(platform)
    if adapter:
        creds = await resolve_creds(platform, wid)
        if creds_configured(creds, platform):
            # Real sync (TradeMe): fetches live comparables and queues pending suggestions.
            try:
                return await adapter.sync(wid, conn)
            except Exception as e:
                await log_event(wid, EventType.AI_ERROR, f"{platform} sync failed", {"error": str(e)})
                raise HTTPException(status_code=502, detail=f"{platform} sync failed: {e}")
    # Legacy simulated sync (structure-only connector).
    now = datetime.now(timezone.utc).isoformat()
    await db.integrations.update_one({"platform": platform, "workspace_id": wid}, {"$set": {"last_sync": now}})
    await log_event(wid, EventType.CONNECTOR_SYNC_EXECUTED, f"Sync executed for {platform}", {"platform": platform})
    await log_event(wid, EventType.EXTERNAL_DATA_RECEIVED, f"Simulated market data received from {platform}", {"platform": platform, "simulated": True})
    await log_event(wid, EventType.SYNC_ACTION_QUEUED, f"{platform} sync produced pending actions for approval", {"platform": platform})
    return {"platform": platform, "last_sync": now, "simulated": True, "note": "Structure-only connector. Live API integration not enabled; all external actions require approval."}


@router.post("/integrations/{platform}/disconnect")
async def disconnect_integration(platform: str, wid: str = Depends(get_wid)):
    """Clear saved credentials and reset to disconnected (Connection Wizard step)."""
    await seed_connectors(wid)
    await db.integrations.update_one(
        {"platform": platform, "workspace_id": wid},
        {"$set": {"auth_status": "disconnected", "sync_enabled": False, "last_test": None},
         "$unset": {"setup": "", "config": "", "tokens": ""}},
    )
    await log_event(wid, EventType.CONNECTOR_AUTH_REVOKED, f"Disconnected {platform}", {"platform": platform})
    return {"platform": platform, "auth_status": "disconnected"}
