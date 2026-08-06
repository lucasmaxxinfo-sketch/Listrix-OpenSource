import json
import logging

from fastapi import APIRouter, Depends, HTTPException

from deps import db, get_wid, rate_limit_llm
from models import AssistantRequest
from services import llm
from services.events import EventType, log_event
from services.memory import build_ai_memory, memory_block

logger = logging.getLogger(__name__)

router = APIRouter()

ASSISTANT_SYSTEM = ("You are Listrix, a real-time marketing manager for a resale business, speaking to the owner. Use the business AI memory to "
                    "personalise. Answers are SHORT and spoken-style (1-3 sentences). You NEVER execute changes \u2014 you only recommend; the owner "
                    "approves every action. You ALWAYS respond with a single valid JSON object and nothing else.")


@router.post("/ai/assistant")
async def ai_assistant(payload: AssistantRequest, wid: str = Depends(get_wid), _rl: None = Depends(rate_limit_llm)):
    if payload.voice:
        await log_event(wid, EventType.VOICE_QUERY_RECEIVED, f"Voice query: {payload.query}", {"query": payload.query})
    mem = await build_ai_memory(wid)
    if payload.item_id:
        item = await db.items.find_one({"id": payload.item_id, "workspace_id": wid}, {"_id": 0, "image": 0})
        listing = await db.listings.find_one({"workspace_id": wid, "$or": [{"item_id": payload.item_id}, {"source_name": (item or {}).get("name")}]}, {"_id": 0}, sort=[("created_at", -1)]) if item else None
        perf = await db.performance.find_one({"item_id": payload.item_id, "workspace_id": wid}, {"_id": 0})
        pend = await db.suggestions.find({"item_id": payload.item_id, "workspace_id": wid, "status": "pending"}, {"_id": 0}).to_list(10)
        context = {"item": item, "listing": listing, "performance": perf, "pending_suggestions": pend}
    else:
        context = {"total_items": await db.items.count_documents({"workspace_id": wid}),
                   "total_listings": await db.listings.count_documents({"workspace_id": wid}),
                   "pending_suggestions": await db.suggestions.count_documents({"workspace_id": wid, "status": "pending"}),
                   "struggling_items": [p["item_name"] for p in await db.performance.find({"workspace_id": wid, "status": "poor"}, {"_id": 0, "item_name": 1}).to_list(20)]}
    prompt = (f"{memory_block(mem)}\nOwner's question: \"{payload.query}\"\n\nBusiness context: {json.dumps(context, default=str)}\n\n"
              'Respond with ONLY JSON: { "answer": string, "recommendations": [ {"title":string,"detail":string,"urgency":"low"|"medium"|"high","confidence":number} ] }')
    try:
        data = await llm.call_llm(ASSISTANT_SYSTEM, prompt)
        recs = []
        for r in (data.get("recommendations") or [])[:5]:
            u = str(r.get("urgency", "medium")).lower()
            recs.append({"title": str(r.get("title", "")).strip(), "detail": str(r.get("detail", "")).strip(),
                         "urgency": u if u in ("low", "medium", "high") else "medium", "confidence": float(r.get("confidence", 60))})
        return {"answer": str(data.get("answer", "")).strip(), "recommendations": recs}
    except Exception as e:
        logger.error(f"Assistant failed: {e}")
        raise HTTPException(status_code=500, detail=f"Assistant failed: {e}")
    finally:
        if payload.voice:
            await log_event(wid, EventType.VOICE_QUERY_PROCESSED, f"Voice query processed: {payload.query[:60]}", None)
