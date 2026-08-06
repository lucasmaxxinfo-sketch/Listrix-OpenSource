import logging

from fastapi import APIRouter, Depends, HTTPException

from deps import db, get_wid, rate_limit_llm
from models import VisionRequest
from services import llm
from services.events import EventType, log_event
from services.vision import VISION_SYSTEM, build_vision_prompt, parse_vision_result

logger = logging.getLogger(__name__)

router = APIRouter()

# Cap the vision payload: a large base64 image is counted as tokens by LLM providers
# and blows past the model context window (a 5MB photo ~ 6.7MB base64 ~ 1.6M tokens).
MAX_VISION_IMAGE_CHARS = 2_000_000


@router.post("/ai/vision/analyze")
async def vision_analyze(payload: VisionRequest, wid: str = Depends(get_wid), _rl: None = Depends(rate_limit_llm)):
    if payload.image and len(payload.image) > MAX_VISION_IMAGE_CHARS:
        raise HTTPException(status_code=400, detail="Image is too large for analysis. Use a smaller or compressed photo.")
    try:
        data = await llm.call_llm(VISION_SYSTEM, build_vision_prompt(payload.hint), image_b64=payload.image)
        result = parse_vision_result(data)
        await log_event(wid, EventType.IMAGE_ANALYSED, f"Image analysed: {result['item_type'] or 'item'}", {"item_type": result["item_type"], "category": result["category"]})
        await log_event(wid, EventType.VALUE_ESTIMATED, f"Value estimated: ${result['value_estimate']['low']}-${result['value_estimate']['high']}", {"value_estimate": result["value_estimate"]})
        if payload.item_id:
            await db.items.update_one({"id": payload.item_id, "workspace_id": wid}, {"$set": {
                "vision": {k: result[k] for k in ("item_type", "category", "brand", "condition_guess", "features")},
                "value_estimate": result["value_estimate"], "category": result["category"]}})
        return result
    except Exception as e:
        logger.error(f"Vision analysis failed: {e}")
        await log_event(wid, EventType.AI_ERROR, "Vision analysis failed", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Vision analysis failed: {e}")
