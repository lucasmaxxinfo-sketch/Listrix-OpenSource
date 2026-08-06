import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from deps import db, get_wid, rate_limit_llm
from models import GenerateRequest, Listing
from services.events import EventType, log_event
from services.listing import generate_listing_ai
from utils import parse_iso

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ai/generate", response_model=Listing)
async def ai_generate(payload: GenerateRequest, wid: str = Depends(get_wid), _rl: None = Depends(rate_limit_llm)):
    try:
        result = await generate_listing_ai(wid, payload)
        listing = Listing(workspace_id=wid, item_id=payload.item_id, source_name=payload.name, **result)
        doc = listing.model_dump()
        doc["created_at"] = doc["created_at"].isoformat()
        await db.listings.insert_one({**doc})
        await log_event(wid, EventType.LISTING_GENERATED, f"AI listing generated for: {payload.name}", {"listing_id": listing.id, "listing_title": listing.listing_title, "suggested_price": listing.suggested_price})
        return listing
    except Exception as e:
        logger.error(f"AI generation failed: {e}")
        await log_event(wid, EventType.AI_ERROR, f"AI generation failed for: {payload.name}", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"AI generation failed: {e}")


@router.get("/listings", response_model=List[Listing])
async def get_listings(wid: str = Depends(get_wid), limit: int = 100):
    rows = await db.listings.find({"workspace_id": wid}, {"_id": 0}).sort("created_at", -1).to_list(limit)
    for ls in rows:
        ls["created_at"] = parse_iso(ls.get("created_at"))
    return rows
