from fastapi import APIRouter, Depends

from deps import db, get_wid

router = APIRouter()


@router.get("/notifications")
async def list_notifications(wid: str = Depends(get_wid), limit: int = 50, unread: bool = False):
    query = {"workspace_id": wid}
    if unread:
        query["read"] = False
    return await db.notifications.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)


@router.post("/notifications/read")
async def mark_all_read(wid: str = Depends(get_wid)):
    r = await db.notifications.update_many({"workspace_id": wid, "read": False}, {"$set": {"read": True}})
    return {"marked": r.modified_count}


@router.post("/notifications/{notification_id}/read")
async def mark_read(notification_id: str, wid: str = Depends(get_wid)):
    await db.notifications.update_one({"id": notification_id, "workspace_id": wid}, {"$set": {"read": True}})
    return {"ok": True}
