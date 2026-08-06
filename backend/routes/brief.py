import json
import logging

from fastapi import APIRouter, Depends, HTTPException

from deps import db, get_wid, rate_limit_llm
from models import Brief
from services import llm
from services.events import EventType, log_event
from services.memory import build_ai_memory, memory_block
from utils import parse_iso

logger = logging.getLogger(__name__)

router = APIRouter()

BRIEF_SYSTEM = ("You are the head of marketing writing a concise Daily AI Briefing for the owner. Use business AI memory to personalise. Completed-sale "
                "data is not tracked; frame around listing readiness, pricing and activity. You ALWAYS respond with a single valid JSON object and nothing else.")


@router.post("/brief/generate", response_model=Brief)
async def generate_brief(wid: str = Depends(get_wid), _rl: None = Depends(rate_limit_llm)):
    items = await db.items.find({"workspace_id": wid}, {"_id": 0, "image": 0}).to_list(200)
    listings = await db.listings.find({"workspace_id": wid}, {"_id": 0}).to_list(200)
    perf = await db.performance.find({"workspace_id": wid}, {"_id": 0}).to_list(200)
    pending = await db.suggestions.count_documents({"workspace_id": wid, "status": "pending"})
    applied = await db.suggestions.count_documents({"workspace_id": wid, "status": "applied"})
    ln = {l.get("source_name") for l in listings}
    li = {l.get("item_id") for l in listings}
    without = [it["name"] for it in items if it["name"] not in ln and it["id"] not in li]
    poor = [p["item_name"] for p in perf if p.get("status") == "poor"]
    good = [p["item_name"] for p in perf if p.get("status") == "good"]
    agg = {"total_items": len(items), "total_listings": len(listings), "items_without_listing": without[:10], "poor_performers": poor[:10],
           "good_performers": good[:10], "pending_suggestions": pending, "applied_suggestions": applied,
           "avg_price": round(sum(l.get("suggested_price", 0) for l in listings) / len(listings), 2) if listings else None}
    mem = await build_ai_memory(wid)
    prompt = (f"{memory_block(mem)}\nWrite today's Daily AI Briefing using these aggregates:\n{json.dumps(agg, indent=2)}\n\n"
              'Respond with ONLY JSON with keys: headline, summary, what_sold, what_didnt_sell, priority_items[], suggested_actions[], risk_alerts[], opportunities[]')
    try:
        data = await llm.call_llm(BRIEF_SYSTEM, prompt)
        brief = Brief(workspace_id=wid, headline=str(data.get("headline", "Daily AI Briefing")).strip(), summary=str(data.get("summary", "")).strip(),
                      what_sold=str(data.get("what_sold", "")).strip(), what_didnt_sell=str(data.get("what_didnt_sell", "")).strip(),
                      priority_items=[str(x) for x in (data.get("priority_items") or [])][:8],
                      suggested_actions=[str(x) for x in (data.get("suggested_actions") or [])][:8],
                      risk_alerts=[str(x) for x in (data.get("risk_alerts") or [])][:8],
                      opportunities=[str(x) for x in (data.get("opportunities") or [])][:8])
        bd = brief.model_dump()
        bd["created_at"] = bd["created_at"].isoformat()
        await db.briefs.insert_one({**bd})
        await log_event(wid, EventType.AI_BRIEFING_GENERATED, "Daily AI Briefing generated", {"headline": brief.headline})
        await log_event(wid, EventType.DAILY_BRIEF_GENERATED, "Daily Operating Brief generated", {"headline": brief.headline})
        return brief
    except Exception as e:
        logger.error(f"Brief failed: {e}")
        await log_event(wid, EventType.AI_ERROR, "Daily AI Briefing generation failed", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Brief generation failed: {e}")


@router.get("/brief/latest")
async def latest_brief(wid: str = Depends(get_wid)):
    row = await db.briefs.find_one({"workspace_id": wid}, {"_id": 0}, sort=[("created_at", -1)])
    if not row:
        return None
    row["created_at"] = parse_iso(row.get("created_at"))
    return row
