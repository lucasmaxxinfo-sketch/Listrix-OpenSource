import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from deps import db, get_wid
from services.events import EventType, log_event
from services.integrations import get_adapter

router = APIRouter()


class ReplyRequest(BaseModel):
    text: str


async def _gmail_sync(wid):
    """Pull real buyer messages via the Gmail adapter when configured + connected."""
    adapter = get_adapter("Gmail")
    if not adapter or not adapter.is_configured():
        return 0
    conn = await db.integrations.find_one({"platform": "Gmail", "workspace_id": wid}, {"_id": 0})
    if not conn or conn.get("auth_status") != "connected":
        return 0
    try:
        result = await adapter.sync(wid, conn)
        return int(result.get("messages_imported", 0))
    except Exception as e:
        await log_event(wid, EventType.AI_ERROR, "Gmail sync failed", {"error": str(e)})
        return 0


@router.post("/inbox/refresh")
async def refresh_inbox(wid: str = Depends(get_wid)):
    await db.inbox.delete_many({"workspace_id": wid})
    perf = await db.performance.find({"workspace_id": wid}, {"_id": 0}).to_list(200)
    pending = await db.suggestions.find({"workspace_id": wid, "status": "pending"}, {"_id": 0}).sort("confidence", -1).to_list(50)
    items = await db.items.find({"workspace_id": wid}, {"_id": 0, "image": 0}).sort("created_at", -1).to_list(50)
    msgs = []
    for p in perf:
        if p.get("status") == "poor":
            msgs.append({"type": "AI_ALERT", "priority": "high", "title": f"{p['item_name']} underperforming", "body": p.get("reason", "At risk of not selling."), "suggested_action": p.get("recommended_action", "Review pricing and listing."), "related_item_id": p["item_id"], "related_item_name": p["item_name"]})
        elif p.get("status") == "good":
            msgs.append({"type": "OPPORTUNITY", "priority": "medium", "title": f"{p['item_name']} is a strong performer", "body": f"High sell likelihood ({p.get('likelihood_of_sale', 0):.0f}%).", "suggested_action": "Feature or bundle this item.", "related_item_id": p["item_id"], "related_item_name": p["item_name"]})
    for s in pending[:5]:
        msgs.append({"type": "ACTION_RECOMMENDED", "priority": ("high" if s.get("risk_level") == "high" else "medium"), "title": s["title"], "body": s.get("detail", ""), "suggested_action": s.get("expected_outcome", "Review in Action Queue."), "related_item_id": s.get("item_id"), "related_item_name": s.get("item_name")})
    if not msgs and items:
        msgs.append({"type": "SYSTEM", "priority": "low", "title": "Welcome to your operations inbox", "body": "Alerts, opportunities and buyer messages will appear here as you add items and run analysis.", "suggested_action": None, "related_item_id": None, "related_item_name": None})
    for m in msgs:
        m.update({"id": str(uuid.uuid4()), "workspace_id": wid, "read": False, "reply_draft": None,
                  "created_at": datetime.now(timezone.utc).isoformat()})
        await db.inbox.insert_one({**m})
        await log_event(wid, EventType.INBOX_MESSAGE_RECEIVED, f"Inbox: {m['title']}", {"type": m["type"], "priority": m["priority"]})
    gmail_imported = await _gmail_sync(wid)
    count = len(msgs) + gmail_imported
    return {"count": count, "gmail_imported": gmail_imported}


@router.get("/inbox")
async def get_inbox(wid: str = Depends(get_wid)):
    rows = await db.inbox.find({"workspace_id": wid}, {"_id": 0}).to_list(200)
    order = {"high": 0, "medium": 1, "low": 2}
    rows.sort(key=lambda m: (order.get(m.get("priority"), 3), m.get("created_at", "")))
    return rows


@router.post("/inbox/{message_id}/read")
async def mark_message_read(message_id: str, wid: str = Depends(get_wid)):
    r = await db.inbox.update_one({"id": message_id, "workspace_id": wid}, {"$set": {"read": True}})
    if r.modified_count == 0 and r.matched_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"ok": True}


@router.post("/inbox/{message_id}/reply")
async def draft_reply(message_id: str, payload: ReplyRequest, wid: str = Depends(get_wid)):
    msg = await db.inbox.find_one({"id": message_id, "workspace_id": wid}, {"_id": 0})
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Reply text must not be empty")
    await db.inbox.update_one({"id": message_id, "workspace_id": wid}, {"$set": {"reply_draft": payload.text.strip(), "read": True}})
    await log_event(wid, EventType.INBOX_REPLY_DRAFTED, f"Reply drafted for: {msg['title']}",
                    {"message_id": message_id, "draft": payload.text.strip()[:120]})
    return {"ok": True, "message_id": message_id, "reply_draft": payload.text.strip()}
