import re

from fastapi import APIRouter, Depends

from deps import db, get_wid

router = APIRouter()


@router.get("/search")
async def global_search(q: str, wid: str = Depends(get_wid), limit: int = 10):
    query = q.strip()
    if len(query) < 2:
        return {"query": q, "count": 0, "results": []}
    rx = re.escape(query)

    async def find(collection, fields):
        clauses = [{f: {"$regex": rx, "$options": "i"}} for f in fields]
        return await db[collection].find({"workspace_id": wid, "$or": clauses}, {"_id": 0}).sort("created_at", -1).to_list(limit)

    items = await find("items", ["name", "description", "category"])
    listings = await find("listings", ["listing_title", "source_name"])
    events = await find("events", ["message"])
    inbox = await find("inbox", ["title", "body"])

    results = (
        [{"type": "item", "id": it["id"], "title": it["name"], "subtitle": it.get("category") or it.get("condition") or "", "link": f"/items/{it['id']}"} for it in items]
        + [{"type": "listing", "id": l["id"], "title": l["listing_title"], "subtitle": l.get("source_name") or "", "link": f"/items/{l['item_id']}" if l.get("item_id") else ""} for l in listings]
        + [{"type": "event", "id": e["id"], "title": e["message"], "subtitle": e.get("type") or "", "link": ""} for e in events]
        + [{"type": "inbox", "id": m["id"], "title": m["title"], "subtitle": m.get("body") or "", "link": "/inbox"} for m in inbox]
    )
    return {"query": q, "count": len(results), "results": results[:60]}
