"""Idempotent bootstrap migrations: default workspace + legacy data backfill."""
import logging

logger = logging.getLogger(__name__)


async def ensure_default_workspace():
    # lazy imports avoid a circular dependency (deps -> migrations -> deps)
    from config import SCOPED
    from deps import db
    from models import Workspace

    ws = await db.workspaces.find_one({"is_default": True}, {"_id": 0})
    if ws:
        return ws
    ws = await db.workspaces.find_one({}, {"_id": 0})
    if ws:
        return ws
    default = Workspace(name="My Business", is_default=True)
    doc = default.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.workspaces.insert_one({**doc})
    # migrate any pre-existing unscoped data into the default workspace
    for col in SCOPED:
        await db[col].update_many({"workspace_id": {"$exists": False}}, {"$set": {"workspace_id": default.id}})
    return doc
