import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from deps import db, get_wid
from models import GenerateRequest, Listing, ModifyRequest, Suggestion
from services.events import EventType, log_event
from services.listing import generate_listing_ai
from services.marketing_agent import record_feedback
from utils import parse_iso

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/suggestions", response_model=List[Suggestion])
async def get_suggestions(wid: str = Depends(get_wid), status: Optional[str] = None, item_id: Optional[str] = None):
    q = {"workspace_id": wid}
    if status:
        q["status"] = status
    if item_id:
        q["item_id"] = item_id
    rows = await db.suggestions.find(q, {"_id": 0}).sort("confidence", -1).to_list(300)
    for r in rows:
        r["created_at"] = parse_iso(r.get("created_at"))
        if r.get("applied_at"):
            r["applied_at"] = parse_iso(r.get("applied_at"))
        if r.get("dismissed_at"):
            r["dismissed_at"] = parse_iso(r.get("dismissed_at"))
    return rows


@router.post("/suggestions/{sugg_id}/apply")
async def apply_suggestion(sugg_id: str, wid: str = Depends(get_wid)):
    sugg = await db.suggestions.find_one({"id": sugg_id, "workspace_id": wid}, {"_id": 0})
    if not sugg:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    if sugg.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Suggestion is not pending")
    item = await db.items.find_one({"id": sugg["item_id"], "workspace_id": wid}, {"_id": 0})
    listing = None
    if sugg.get("listing_id"):
        listing = await db.listings.find_one({"id": sugg["listing_id"], "workspace_id": wid}, {"_id": 0})
    if not listing and item:
        listing = await db.listings.find_one({"workspace_id": wid, "$or": [{"item_id": item["id"]}, {"source_name": item["name"]}]}, {"_id": 0}, sort=[("created_at", -1)])
    st = sugg["type"]
    params = sugg.get("params") or {}
    change = ""
    await log_event(wid, EventType.USER_APPROVED_ACTION, f"User approved: {sugg['title']} ({st}) for {sugg['item_name']}", {"suggestion_id": sugg_id, "type": st})
    try:
        if st == "generate_listing" and item:
            result = await generate_listing_ai(wid, GenerateRequest(name=item["name"], description=item["description"], condition=item["condition"], cost=item.get("cost"), item_id=item["id"]))
            nl = Listing(workspace_id=wid, item_id=item["id"], source_name=item["name"], **result)
            nd = nl.model_dump()
            nd["created_at"] = nd["created_at"].isoformat()
            await db.listings.insert_one({**nd})
            await log_event(wid, EventType.LISTING_GENERATED, f"AI listing generated for: {item['name']}", {"listing_id": nl.id})
            change = "Generated a new listing"
        elif st == "reduce_price" and listing and params.get("new_price") is not None:
            op = listing.get("suggested_price")
            np = float(params["new_price"])
            await db.listings.update_one({"id": listing["id"], "workspace_id": wid}, {"$set": {"suggested_price": np}})
            await db.price_history.insert_one({"id": str(uuid.uuid4()), "workspace_id": wid, "item_id": sugg["item_id"], "listing_id": listing["id"], "old_price": op, "new_price": np, "reason": sugg.get("title"), "created_at": datetime.now(timezone.utc).isoformat()})
            await log_event(wid, EventType.PRICE_UPDATED, f"Price for {sugg['item_name']}: ${op} -> ${np}", {"item_id": sugg["item_id"]})
            change = f"Price reduced to ${np}"
        elif st == "improve_title" and listing and params.get("new_title"):
            await db.listings.update_one({"id": listing["id"], "workspace_id": wid}, {"$set": {"listing_title": str(params["new_title"]).strip()}})
            change = "Updated listing title"
        elif st == "add_keywords" and listing and params.get("add_hashtags"):
            ex = listing.get("hashtags", []) or []
            add = [str(t).lstrip("#").strip() for t in params["add_hashtags"] if str(t).strip()]
            await db.listings.update_one({"id": listing["id"], "workspace_id": wid}, {"$set": {"hashtags": list(dict.fromkeys(ex + add))}})
            change = f"Added {len(add)} keyword(s)"
        elif st == "add_urgency" and listing:
            u = str(params.get("urgency_text", "Limited time offer \u2014 priced to sell fast!")).strip()
            d = listing.get("listing_description", "")
            if u not in d:
                d = f"{d}\n\n{u}"
            await db.listings.update_one({"id": listing["id"], "workspace_id": wid}, {"$set": {"listing_description": d}})
            change = "Added urgency messaging"
        elif st == "relist" and item:
            await db.items.update_one({"id": item["id"], "workspace_id": wid}, {"$set": {"listed_at": datetime.now(timezone.utc).isoformat()}, "$inc": {"times_relisted": 1}})
            change = "Item relisted"
        else:
            change = "Marked as applied"
        await db.suggestions.update_one({"id": sugg_id, "workspace_id": wid}, {"$set": {"status": "applied", "applied_at": datetime.now(timezone.utc).isoformat()}})
        await record_feedback(wid, sugg, "approved", change)
        await log_event(wid, EventType.ACTION_APPROVED, f"Action approved: {sugg['title']} for {sugg['item_name']}", {"type": st})
        await log_event(wid, EventType.AI_SUGGESTION_APPLIED, f"Applied '{sugg['title']}' for {sugg['item_name']} \u2014 {change}", {"type": st, "change": change})
        return {"status": "applied", "change": change}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Apply failed: {e}")
        raise HTTPException(status_code=500, detail=f"Apply failed: {e}")


@router.post("/suggestions/{sugg_id}/dismiss")
async def dismiss_suggestion(sugg_id: str, wid: str = Depends(get_wid)):
    sugg = await db.suggestions.find_one({"id": sugg_id, "workspace_id": wid}, {"_id": 0})
    if not sugg:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    await db.suggestions.update_one({"id": sugg_id, "workspace_id": wid}, {"$set": {"status": "dismissed", "dismissed_at": datetime.now(timezone.utc).isoformat()}})
    await record_feedback(wid, sugg, "rejected", "dismissed")
    await log_event(wid, EventType.ACTION_REJECTED, f"Action rejected: {sugg['title']} for {sugg['item_name']}", {"type": sugg.get("type")})
    return {"status": "dismissed"}


@router.post("/suggestions/{sugg_id}/edit")
async def edit_suggestion(sugg_id: str, payload: ModifyRequest, wid: str = Depends(get_wid)):
    sugg = await db.suggestions.find_one({"id": sugg_id, "workspace_id": wid}, {"_id": 0})
    if not sugg:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    if sugg.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Only pending actions can be modified")
    updates = {}
    if payload.detail is not None:
        updates["detail"] = payload.detail
    if payload.params is not None:
        updates["params"] = {**(sugg.get("params") or {}), **payload.params}
    if updates:
        await db.suggestions.update_one({"id": sugg_id, "workspace_id": wid}, {"$set": updates})
    return {"status": "modified", **updates}
