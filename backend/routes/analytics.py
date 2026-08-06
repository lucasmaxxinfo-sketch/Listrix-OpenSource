from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from deps import db, get_wid

router = APIRouter()


@router.get("/analytics")
async def event_analytics(wid: str = Depends(get_wid), days: int = 30):
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    events = await db.events.find({"workspace_id": wid, "created_at": {"$gte": since}}, {"_id": 0}).to_list(2000)
    by_type = Counter(e.get("type") or "UNKNOWN" for e in events)
    by_day = Counter((e.get("created_at") or "")[:10] for e in events if e.get("created_at"))
    items = await db.items.count_documents({"workspace_id": wid})
    sold = await db.items.count_documents({"workspace_id": wid, "sold": True})
    listings = await db.listings.count_documents({"workspace_id": wid})
    pending = await db.suggestions.count_documents({"workspace_id": wid, "status": "pending"})
    return {
        "days": days,
        "events_total": len(events),
        "top_event_types": [{"type": k, "count": v} for k, v in by_type.most_common(8)],
        "events_by_day": [{"day": d, "count": c} for d, c in sorted(by_day.items())],
        "totals": {"items": items, "sold": sold, "listings": listings, "pending_actions": pending},
    }
