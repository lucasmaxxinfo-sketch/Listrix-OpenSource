import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

import config
from db.migrations import ensure_default_workspace
from deps import db, get_current_user, get_wid
from models import Item, Workspace, WorkspaceUpdate
from services.events import EventType, log_event
from utils import parse_iso

router = APIRouter()


def _workspace_filter(user):
    """Workspace visibility: authenticated users see their own (+ legacy ownerless in grace mode)."""
    if user is None:
        return {}
    if config.AUTH_REQUIRED:
        return {"owner_id": user["id"]}
    return {"$or": [{"owner_id": user["id"]}, {"owner_id": {"$exists": False}}]}


async def _owned_or_legacy(ws_id: str, user):
    ws = await db.workspaces.find_one({"id": ws_id}, {"_id": 0})
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if user is not None:
        owner = ws.get("owner_id")
        if owner and owner != user["id"]:
            raise HTTPException(status_code=403, detail="Workspace does not belong to the authenticated user")
        if not owner and config.AUTH_REQUIRED:
            raise HTTPException(status_code=403, detail="Workspace has no owner")
    return ws


@router.get("/")
async def root():
    return {"message": "Listrix API is running"}


@router.get("/workspaces")
async def list_workspaces(user: dict = Depends(get_current_user)):
    await ensure_default_workspace()
    rows = await db.workspaces.find(_workspace_filter(user), {"_id": 0}).sort("created_at", 1).to_list(100)
    for r in rows:
        r["created_at"] = parse_iso(r.get("created_at"))
    return rows


@router.post("/workspaces", response_model=Workspace)
async def create_workspace(payload: Workspace, user: dict = Depends(get_current_user)):
    data = payload.model_dump()
    if user is not None:
        data["owner_id"] = user["id"]
    ws = Workspace(**{**data, "is_default": False})
    doc = ws.model_dump()
    if doc.get("owner_id") is None:
        doc.pop("owner_id", None)  # keep legacy ownerless docs clean
    doc["created_at"] = doc["created_at"].isoformat()
    await db.workspaces.insert_one({**doc})
    # seed connectors for the new workspace
    for c in config.DEFAULT_CONNECTORS:
        await db.integrations.insert_one({**c, "workspace_id": ws.id, "last_sync": None})
    payload_log = {"workspace": ws.name}
    if user is not None:
        payload_log["owner"] = user["id"]
    await log_event(ws.id, EventType.WORKSPACE_CREATED, f"Workspace created: {ws.name}", payload_log)
    return ws


@router.get("/workspaces/{ws_id}")
async def get_workspace(ws_id: str, user: dict = Depends(get_current_user)):
    ws = await _owned_or_legacy(ws_id, user)
    ws["created_at"] = parse_iso(ws.get("created_at"))
    return ws


@router.put("/workspaces/{ws_id}")
async def update_workspace(ws_id: str, payload: WorkspaceUpdate, user: dict = Depends(get_current_user)):
    await _owned_or_legacy(ws_id, user)
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    res = await db.workspaces.update_one({"id": ws_id}, {"$set": updates})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Workspace not found")
    ws = await db.workspaces.find_one({"id": ws_id}, {"_id": 0})
    ws["created_at"] = parse_iso(ws.get("created_at"))
    return ws


@router.get("/workspaces/{ws_id}/export")
async def export_workspace(ws_id: str, user: dict = Depends(get_current_user)):
    ws = await _owned_or_legacy(ws_id, user)
    ws["created_at"] = parse_iso(ws.get("created_at"))
    out = {"workspace": ws}
    for col in ["items", "listings", "suggestions", "performance", "briefs", "events"]:
        out[col] = await db[col].find({"workspace_id": ws_id}, {"_id": 0}).to_list(1000)
    return out


# ---- CSV import ---------------------------------------------------------------
class ImportRequest(BaseModel):
    csv: str


@router.post("/workspaces/import")
async def import_workspace_items(payload: ImportRequest, wid: str = Depends(get_wid)):
    import csv
    import io

    rows = list(csv.DictReader(io.StringIO(payload.csv)))
    created = 0
    skipped = 0
    errors = []
    for idx, row in enumerate(rows, start=2):
        name = (row.get("name") or "").strip()
        if not name:
            skipped += 1
            errors.append(f"row {idx}: missing name")
            continue
        cost_raw = (row.get("cost") or "").strip()
        try:
            cost = float(cost_raw) if cost_raw else None
        except ValueError:
            skipped += 1
            errors.append(f"row {idx}: invalid cost {cost_raw!r}")
            continue
        item = Item(
            workspace_id=wid, name=name,
            description=(row.get("description") or "").strip() or "Imported item",
            condition=(row.get("condition") or "").strip() or "Good",
            cost=cost, category=(row.get("category") or "").strip() or None,
        )
        doc = item.model_dump()
        doc["created_at"] = doc["created_at"].isoformat()
        await db.items.insert_one(doc)
        created += 1
    await log_event(wid, EventType.ITEMS_IMPORTED, f"Imported {created} item(s) via CSV", {"created": created, "skipped": skipped})
    return {"imported": created, "skipped": skipped, "errors": errors[:20]}


# ---- workspace members (multi-user roles, staged) ------------------------------
async def _require_owner(ws_id: str, user):
    ws = await _owned_or_legacy(ws_id, user)
    if user is not None and ws.get("owner_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Only the workspace owner can perform this action")
    return ws


class MemberInvite(BaseModel):
    email: str
    role: str = "member"


@router.get("/workspaces/{ws_id}/members")
async def list_members(ws_id: str, user: dict = Depends(get_current_user)):
    ws = await db.workspaces.find_one({"id": ws_id}, {"_id": 0})
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if user is not None:
        is_owner = ws.get("owner_id") == user["id"]
        member = await db.workspace_members.find_one({"workspace_id": ws_id, "user_id": user["id"]}, {"_id": 0})
        if not is_owner and not member:
            raise HTTPException(status_code=403, detail="Not a member of this workspace")
    return await db.workspace_members.find({"workspace_id": ws_id}, {"_id": 0}).sort("created_at", 1).to_list(100)


@router.post("/workspaces/{ws_id}/members")
async def invite_member(ws_id: str, payload: MemberInvite, user: dict = Depends(get_current_user)):
    await _require_owner(ws_id, user)
    email = payload.email.strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    role = payload.role if payload.role in ("owner", "member", "viewer") else "member"
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    member = {
        "id": str(uuid.uuid4()), "workspace_id": ws_id,
        "user_id": existing_user["id"] if existing_user else None,
        "email": email, "role": role,
        "status": "active" if existing_user else "invited",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.workspace_members.insert_one(member)
    member.pop("_id", None)  # insert_one mutates the dict with a Mongo _id; never leak it
    await log_event(ws_id, EventType.WORKSPACE_CREATED, f"Member invited: {email}", {"email": email, "role": role})
    return member


@router.delete("/workspaces/{ws_id}/members/{user_id}")
async def remove_member(ws_id: str, user_id: str, user: dict = Depends(get_current_user)):
    await _require_owner(ws_id, user)
    ws = await _owned_or_legacy(ws_id, user)
    if ws.get("owner_id") == user_id:
        raise HTTPException(status_code=400, detail="Cannot remove the workspace owner")
    r = await db.workspace_members.delete_one({"workspace_id": ws_id, "$or": [{"user_id": user_id}, {"id": user_id}]})
    if r.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Member not found")
    await log_event(ws_id, EventType.WORKSPACE_CREATED, f"Member removed: {user_id}", {"user_id": user_id})
    return {"ok": True}
