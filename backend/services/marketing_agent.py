"""Marketing Intelligence Agent: per-item analysis, simulation helpers, suggestion generation."""
import logging
import uuid
from datetime import datetime, timezone

from config import SUGGESTION_TYPES
from deps import db
from models import Performance, Suggestion
from services import llm
from services.events import EventType, log_event
from services.memory import build_ai_memory, memory_block
from utils import _seed, hours_since

logger = logging.getLogger(__name__)

AGENT_SYSTEM = ("You are the Marketing Intelligence Agent inside a resale business \u2014 an experienced marketing manager and pricing analyst, "
                "not a chatbot. Use the business AI memory to personalise. Completed-sale data is not tracked; judge likelihood from listing "
                "quality, price vs value/cost, condition, photos, time on market, and market signals. Never repeat dismissed suggestions. "
                "You ALWAYS respond with a single valid JSON object and nothing else.")


def build_agent_prompt(mem, item, listing, memory):
    ls = "No listing generated yet." if not listing else (
        f"Listing title: {listing.get('listing_title')}\nDescription: {listing.get('listing_description')}\n"
        f"Current price: {listing.get('suggested_price')}\nHashtags: {', '.join(listing.get('hashtags', []))}\n")
    vision = item.get("vision") or {}
    ve = item.get("value_estimate") or {}
    ms = item.get("market_signal") or {}
    lc = item.get("lifecycle") or {}
    extra = ""
    if vision:
        extra += f"AI vision: type={vision.get('item_type')}, category={vision.get('category')}, brand={vision.get('brand')}, features={vision.get('features')}\n"
    if ve:
        extra += f"Value estimate: low={ve.get('low')} mid={ve.get('mid')} high={ve.get('high')} conf={ve.get('confidence')}\n"
    if ms:
        extra += f"Market signal: demand={ms.get('demand')}, competition={ms.get('competition')}, saturation={ms.get('saturation_pct')}%, trend={ms.get('price_trend')}\n"
    if lc:
        extra += f"Lifecycle: views={lc.get('views')}, engagement={lc.get('engagement')}, conversion={lc.get('conversion_likelihood')}\n"
    return (
        f"{memory_block(mem)}\nAnalyse this inventory item.\n\nITEM\nName: {item.get('name')}\nDescription: {item.get('description')}\n"
        f"Condition: {item.get('condition')}\nSeller cost: {item.get('cost')}\nHas photo: {bool(item.get('image'))}\n"
        f"Times relisted: {item.get('times_relisted', 0)}\n{extra}\nLISTING\n{ls}\n"
        f"MEMORY\nTime on market (hrs): {memory.get('time_on_market_hours')}\nPrice changes: {memory.get('price_changes')}\n"
        f"Applied types: {memory.get('applied_types')}\nDismissed types (DO NOT repeat): {memory.get('dismissed_types')}\n\n"
        'Respond with ONLY JSON: { "performance": {"status":"good"|"average"|"poor","likelihood_of_sale":number,"reason":string,"recommended_action":string}, '
        '"suggestions": [ {"type":one of "reduce_price","improve_title","add_keywords","relist","add_urgency","generate_listing","title":string,'
        '"detail":string (action plan),"confidence":number,"expected_impact":string,"expected_outcome":string,"risk_level":"low"|"medium"|"high",'
        '"reason":string,"params":object} ] (2-4, ranked) }\n'
        'params: reduce_price->{"new_price":number}; improve_title->{"new_title":string}; add_keywords->{"add_hashtags":[strings]}; '
        'add_urgency->{"urgency_text":string}; relist->{}; generate_listing->{}. If no listing, top suggestion MUST be generate_listing.')


def simulate_market_signal(item):
    n = _seed(item["id"])
    return {"simulated": True, "demand": ["low", "medium", "high"][n % 3],
            "competition": ["low", "medium", "high"][(n // 3) % 3], "saturation_pct": round(20 + (n % 70), 0),
            "price_trend": ["falling", "stable", "rising"][(n // 7) % 3]}


def simulate_lifecycle(listing, perf):
    if not listing:
        return None
    hrs = hours_since(listing.get("created_at"))
    n = _seed(listing["id"])
    views = int(hrs * (2 + (n % 5)) + (n % 25))
    eng = "low" if views < 30 else "medium" if views < 120 else "high"
    conv = perf.get("likelihood_of_sale") if perf else (40 + (n % 40))
    return {"simulated": True, "time_since_published_hours": hrs, "views": views, "engagement": eng, "conversion_likelihood": round(float(conv), 0)}


async def record_feedback(wid, sugg, action, outcome):
    try:
        await db.feedback.insert_one({"id": str(uuid.uuid4()), "workspace_id": wid, "suggestion_id": sugg.get("id"),
                                      "item_id": sugg.get("item_id"), "type": sugg.get("type"), "action": action,
                                      "outcome": outcome, "created_at": datetime.now(timezone.utc).isoformat()})
    except Exception as e:
        logger.error(f"record_feedback failed: {e}")


async def gather_memory(wid, item, listing):
    iid = item["id"]
    pc = await db.price_history.count_documents({"workspace_id": wid, "item_id": iid})
    applied = await db.suggestions.find({"workspace_id": wid, "item_id": iid, "status": "applied"}, {"_id": 0, "type": 1}).to_list(50)
    dismissed = await db.suggestions.find({"workspace_id": wid, "item_id": iid, "status": "dismissed"}, {"_id": 0, "type": 1}).to_list(50)
    listed_ref = item.get("listed_at") or (listing.get("created_at") if listing else None) or item.get("created_at")
    return {"time_on_market_hours": hours_since(listed_ref), "price_changes": pc,
            "applied_types": list({a["type"] for a in applied}), "dismissed_types": list({d["type"] for d in dismissed})}


def simulate_analysis(wid, item, listing, memory):
    """Rule-based fallback when the local AI model is offline.

    Keeps the AI agent areas usable (clearly labelled as simulated) instead of
    failing with a connection error. Switches back to live analysis automatically
    the moment Ollama is reachable again.
    """
    has_listing = listing is not None
    cost = item.get("cost")
    price = listing.get("suggested_price") if listing else None
    hrs = memory.get("time_on_market_hours", 0)
    if not has_listing:
        status, likelihood, reason = "average", 55.0, "No listing yet - generate one to start gathering market data."
    elif price is not None and cost is not None and price < cost * 1.1:
        status, likelihood, reason = "poor", 35.0, "Price is close to (or below) cost, which usually stalls sales."
    elif price is not None and cost is not None and price > cost * 2:
        status, likelihood, reason = "good", 78.0, "Healthy margin vs cost with solid listing quality."
    elif hrs > 720:
        status, likelihood, reason = "poor", 42.0, "On market for a while - consider a price or title refresh."
    else:
        status, likelihood, reason = "average", 60.0, "Listed with reasonable fundamentals; watch early engagement."

    suggestions = []
    if not has_listing:
        suggestions.append({
            "type": "generate_listing", "title": "Generate a listing", "detail": "Create a marketplace listing for this item to start attracting buyers.",
            "confidence": 90, "expected_impact": "Starts buyer interest", "expected_outcome": "Listing live with title, description and hashtags",
            "risk_level": "low", "reason": "Items without listings cannot sell.", "params": {},
        })
    elif price is not None and cost is not None and price < cost * 1.25:
        suggestions.append({
            "type": "reduce_price", "title": "Reconsider the price", "detail": "Margin over cost is thin; check comparable listings before lowering.",
            "confidence": 70, "expected_impact": "Faster sale", "expected_outcome": "Better buyer response",
            "risk_level": "medium", "reason": "Thin margin can stall negotiations.", "params": {"new_price": round(float(cost) * 1.4, 2)},
        })
    if has_listing and hrs > 336:
        suggestions.append({
            "type": "relist", "title": "Refresh the listing", "detail": "Relist after time on market to regain visibility.",
            "confidence": 68, "expected_impact": "Renewed visibility", "expected_outcome": "Fresh reach among buyers",
            "risk_level": "low", "reason": "Stale listings lose rank.", "params": {},
        })
    if len(suggestions) < 2:
        suggestions.append({
            "type": "add_keywords", "title": "Add search keywords", "detail": "Add more hashtags so buyers searching similar items find this faster.",
            "confidence": 62, "expected_impact": "More views", "expected_outcome": "Higher discovery in search",
            "risk_level": "low", "reason": "Discovery drives engagement.", "params": {"add_hashtags": ["vintage", "collectible"]},
        })
    return {"status": status, "likelihood_of_sale": likelihood, "reason": reason,
            "recommended_action": suggestions[0]["title"] if suggestions else "Monitor", "simulated": True}, suggestions


async def analyze_one(wid, item):
    listing = await db.listings.find_one({"workspace_id": wid, "$or": [{"item_id": item["id"]}, {"source_name": item["name"]}]}, {"_id": 0}, sort=[("created_at", -1)])
    memory = await gather_memory(wid, item, listing)
    mem = await build_ai_memory(wid)
    perf_existing = await db.performance.find_one({"workspace_id": wid, "item_id": item["id"]}, {"_id": 0})
    ms = simulate_market_signal(item)
    lc = simulate_lifecycle(listing, perf_existing)
    item["market_signal"] = ms
    item["lifecycle"] = lc
    await db.items.update_one({"id": item["id"], "workspace_id": wid}, {"$set": {"market_signal": ms}})
    await log_event(wid, EventType.MARKET_SIGNAL_UPDATED, f"Market signal for {item['name']}: demand {ms['demand']}, {ms['price_trend']} trend", {"item_id": item["id"]})
    if lc:
        await log_event(wid, EventType.LISTING_VIEW_ESTIMATED, f"Estimated {lc['views']} views for {item['name']} ({lc['engagement']} engagement)", {"item_id": item["id"]})
    simulated = False
    try:
        data = await llm.call_llm(AGENT_SYSTEM, build_agent_prompt(mem, item, listing, memory))
    except Exception as e:
        logger.warning("LLM offline for %s - using simulated analysis: %s", item["name"], e)
        pr, fallback_suggestions = simulate_analysis(wid, item, listing, memory)
        data = {"performance": pr, "suggestions": fallback_suggestions}
        simulated = True
        await log_event(wid, EventType.AI_ERROR, f"AI model offline - simulated analysis used for {item['name']}", {"item_id": item["id"], "simulated": True})

    pr = data.get("performance", {}) or {}
    status = str(pr.get("status", "average")).lower()
    if status not in ("good", "average", "poor"):
        status = "average"
    perf = Performance(workspace_id=wid, item_id=item["id"], item_name=item["name"], status=status,
                       likelihood_of_sale=float(pr.get("likelihood_of_sale", 50)), reason=str(pr.get("reason", "")).strip(),
                       recommended_action=str(pr.get("recommended_action", "")).strip(), time_on_market_hours=memory["time_on_market_hours"])
    pdoc = perf.model_dump()
    pdoc["updated_at"] = pdoc["updated_at"].isoformat()
    await db.performance.replace_one({"workspace_id": wid, "item_id": item["id"]}, pdoc, upsert=True)
    await log_event(wid, EventType.LISTING_PERFORMANCE_UPDATED, f"Performance for {item['name']}: {status} ({perf.likelihood_of_sale:.0f}% likely)", {"item_id": item["id"], "status": status})

    await db.suggestions.delete_many({"workspace_id": wid, "item_id": item["id"], "status": "pending"})
    created = []
    for s in (data.get("suggestions") or [])[:4]:
        st = str(s.get("type", "")).strip()
        if st not in SUGGESTION_TYPES:
            continue
        rl = str(s.get("risk_level", "low")).lower()
        sugg = Suggestion(workspace_id=wid, item_id=item["id"], item_name=item["name"], listing_id=(listing.get("id") if listing else None),
                          type=st, title=str(s.get("title", st)).strip(), detail=str(s.get("detail", "")).strip(),
                          confidence=float(s.get("confidence", 60)), expected_impact=str(s.get("expected_impact", "")).strip(),
                          expected_outcome=str(s.get("expected_outcome", "")).strip(), risk_level=(rl if rl in ("low", "medium", "high") else "low"),
                          reason=str(s.get("reason", "")).strip(), params=s.get("params") or {})
        sdoc = sugg.model_dump()
        sdoc["created_at"] = sdoc["created_at"].isoformat()
        await db.suggestions.insert_one({**sdoc})
        created.append(sugg.model_dump())
    if created:
        await log_event(wid, EventType.ACTION_QUEUED, f"{len(created)} action(s) queued for {item['name']}", {"item_id": item["id"], "count": len(created)})
    await log_event(wid, EventType.AI_SUGGESTION_CREATED, f"{len(created)} suggestion(s) generated for {item['name']}", {"item_id": item["id"]})
    return {"performance": perf.model_dump(), "suggestions": created, "simulated": simulated}
