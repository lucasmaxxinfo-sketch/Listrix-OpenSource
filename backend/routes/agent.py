import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from deps import db, get_wid, rate_limit_llm
from models import Performance
from services.events import EventType, log_event
from services.jobs import create_job, run_analysis_job, spawn
from services.marketing_agent import analyze_one, simulate_market_signal
from utils import parse_iso

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ai/analyze/{item_id}")
async def analyze_item(item_id: str, wid: str = Depends(get_wid), _rl: None = Depends(rate_limit_llm)):
    item = await db.items.find_one({"id": item_id, "workspace_id": wid}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    try:
        return await analyze_one(wid, item)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        await log_event(wid, EventType.AI_ERROR, f"Analysis failed for: {item.get('name')}", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")


@router.post("/ai/analyze-all")
async def analyze_all(wid: str = Depends(get_wid), _rl: None = Depends(rate_limit_llm), limit: int = 12):
    items = await db.items.find({"workspace_id": wid}, {"_id": 0}).sort("created_at", -1).to_list(limit)
    if not items:
        return {"job_id": None, "status": "done", "total": 0, "analyzed": 0}
    job_id = await create_job(wid, "analyze-all", total=len(items))
    spawn(wid, job_id, run_analysis_job(wid, job_id, [it["id"] for it in items]))
    await log_event(wid, EventType.PERFORMANCE_RECALCULATED, f"Queued performance recalculation for {len(items)} item(s)", {"job_id": job_id})
    return {"job_id": job_id, "status": "queued", "total": len(items)}


@router.get("/performance", response_model=List[Performance])
async def get_performance(wid: str = Depends(get_wid)):
    rows = await db.performance.find({"workspace_id": wid}, {"_id": 0}).to_list(200)
    for r in rows:
        r["updated_at"] = parse_iso(r.get("updated_at"))
    return rows


@router.get("/price-history/{item_id}")
async def get_price_history(item_id: str, wid: str = Depends(get_wid)):
    return await db.price_history.find({"workspace_id": wid, "item_id": item_id}, {"_id": 0}).sort("created_at", -1).to_list(100)


@router.get("/market/signals")
async def market_signals(wid: str = Depends(get_wid)):
    items = await db.items.find({"workspace_id": wid}, {"_id": 0, "image": 0}).sort("created_at", -1).to_list(200)
    return [{"item_id": it["id"], "name": it["name"], "market_signal": it.get("market_signal") or simulate_market_signal(it)} for it in items]


@router.get("/performance-intelligence")
async def performance_intelligence(wid: str = Depends(get_wid)):
    items = await db.items.find({"workspace_id": wid}, {"_id": 0, "image": 0}).to_list(200)
    listings = await db.listings.find({"workspace_id": wid}, {"_id": 0}).to_list(200)
    perf = await db.performance.find({"workspace_id": wid}, {"_id": 0}).to_list(200)
    pending = await db.suggestions.find({"workspace_id": wid, "status": "pending"}, {"_id": 0}).sort("confidence", -1).to_list(50)
    price = {}
    for l in listings:
        if l.get("item_id") and l["item_id"] not in price:
            price[l["item_id"]] = l.get("suggested_price")
    ps = sorted(perf, key=lambda p: p.get("likelihood_of_sale", 0), reverse=True)
    best = [{"item_id": p["item_id"], "name": p["item_name"], "likelihood": p["likelihood_of_sale"], "status": p["status"]} for p in ps if p.get("status") == "good"][:5]
    worst = [{"item_id": p["item_id"], "name": p["item_name"], "likelihood": p["likelihood_of_sale"], "status": p["status"]} for p in reversed(ps) if p.get("status") == "poor"][:5]
    needs = [{"item_id": p["item_id"], "name": p["item_name"], "likelihood": p["likelihood_of_sale"], "reason": p.get("reason", "")} for p in ps if p.get("status") in ("poor", "average")][:5]
    nexta = [{"id": s["id"], "item_name": s["item_name"], "title": s["title"], "confidence": s["confidence"], "risk_level": s.get("risk_level", "low"), "type": s["type"]} for s in pending[:6]]
    rev = 0.0
    for it in items:
        p = price.get(it["id"])
        if p is not None and it.get("cost") is not None:
            rev += max(0.0, p - it["cost"])
        elif (it.get("value_estimate") or {}).get("mid"):
            rev += float(it["value_estimate"]["mid"])
    return {"best_performing": best, "worst_performing": worst, "needs_attention": needs, "recommended_next_actions": nexta,
            "predicted_revenue_opportunity": round(rev, 2), "summary": {"items": len(items), "analyzed": len(perf), "pending_actions": len(pending)}}


@router.get("/competitors/{item_id}")
async def get_competitors(item_id: str, wid: str = Depends(get_wid)):
    item = await db.items.find_one({"id": item_id, "workspace_id": wid}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    listing = await db.listings.find_one({"workspace_id": wid, "$or": [{"item_id": item_id}, {"source_name": item["name"]}]}, {"_id": 0}, sort=[("created_at", -1)])
    our_price = listing.get("suggested_price") if listing else item.get("cost")
    positioning = "unknown"
    if our_price is not None and item.get("cost"):
        positioning = "premium" if our_price > item["cost"] * 1.3 else "competitive"
    await log_event(wid, EventType.MARKET_MATCH_FOUND, f"Market positioning computed for {item['name']}: {positioning}", {"item_id": item_id, "simulated": True})
    return {"simulated": True, "note": "Competitor intelligence is architected but external scraping is not enabled yet.",
            "item_id": item_id, "our_price": our_price, "positioning": positioning,
            "comparison_logic": {"signals": ["price_vs_market_median", "condition_adjusted_value", "keyword_overlap", "time_to_sell"], "status": "placeholder"},
            "competitors": []}
