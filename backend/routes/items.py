from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, field_validator

from deps import db, get_wid
from models import Item, ItemCreate
from services.events import EventType, log_event
from services.notifications import notify
from services.storage import store_image
from utils import parse_iso

router = APIRouter()


@router.post("/items", response_model=Item)
async def create_item(payload: ItemCreate, wid: str = Depends(get_wid)):
    now = datetime.now(timezone.utc)
    item = Item(**payload.model_dump(), workspace_id=wid, listed_at=now)
    doc = item.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    doc["listed_at"] = doc["listed_at"].isoformat()
    await db.items.insert_one({**doc})
    await log_event(wid, EventType.ITEM_CREATED, f"Item created: {item.name}", {"id": item.id, "name": item.name, "condition": item.condition, "cost": item.cost})
    return item


@router.get("/items", response_model=List[Item])
async def get_items(wid: str = Depends(get_wid), limit: int = 100):
    items = await db.items.find({"workspace_id": wid}, {"_id": 0}).sort("created_at", -1).to_list(limit)
    for it in items:
        it["created_at"] = parse_iso(it.get("created_at"))
        if it.get("listed_at"):
            it["listed_at"] = parse_iso(it.get("listed_at"))
    return items


@router.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: str, wid: str = Depends(get_wid)):
    it = await db.items.find_one({"id": item_id, "workspace_id": wid}, {"_id": 0})
    if not it:
        raise HTTPException(status_code=404, detail="Item not found")
    it["created_at"] = parse_iso(it.get("created_at"))
    if it.get("listed_at"):
        it["listed_at"] = parse_iso(it.get("listed_at"))
    if it.get("sold_at"):
        it["sold_at"] = parse_iso(it.get("sold_at"))
    return it


STAGES = ("inventory", "listed", "sold", "archived")
ALLOWED_TRANSITIONS = {
    "inventory": ("listed", "sold", "archived"),
    "listed": ("inventory", "sold", "archived"),
    "sold": ("inventory", "archived"),
    "archived": ("inventory", "listed"),
}


class StageRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    stage: str


@router.post("/items/{item_id}/stage", response_model=Item)
async def change_item_stage(item_id: str, payload: StageRequest, wid: str = Depends(get_wid)):
    it = await _find_item(item_id, wid)
    current = it.get("stage") or "inventory"
    target = payload.stage
    if target not in STAGES:
        raise HTTPException(status_code=400, detail=f"Unknown stage: {target}")
    if target == current:
        return {**it, "stage": current}
    if target not in ALLOWED_TRANSITIONS.get(current, ()):
        raise HTTPException(status_code=400, detail=f"Cannot move item from '{current}' to '{target}'")
    await db.items.update_one({"id": item_id, "workspace_id": wid}, {"$set": {"stage": target}})
    await log_event(wid, EventType.ITEM_STAGE_CHANGED, f"Item moved to {target}: {it['name']}",
                    {"id": item_id, "name": it["name"], "from": current, "to": target})
    await notify(wid, f"Item moved to {target}", it["name"], "stage", f"/items/{item_id}")
    return {**it, "stage": target}


class MarkSoldRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    sale_price: float
    sold_at: Optional[str] = None

    @field_validator("sale_price")
    @classmethod
    def non_negative(cls, v):
        if v < 0:
            raise ValueError("sale_price must be >= 0")
        return v


async def _find_item(item_id: str, wid: str):
    it = await db.items.find_one({"id": item_id, "workspace_id": wid}, {"_id": 0})
    if not it:
        raise HTTPException(status_code=404, detail="Item not found")
    return it


class ImageUploadRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    data: str  # data URI or raw base64


@router.post("/items/{item_id}/image", response_model=Item)
async def upload_item_image(item_id: str, payload: ImageUploadRequest, wid: str = Depends(get_wid)):
    it = await _find_item(item_id, wid)
    try:
        image_id = await store_image(wid, payload.data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image data: {e}")
    await db.items.update_one({"id": item_id, "workspace_id": wid}, {"$set": {"image_id": image_id}})
    await log_event(wid, EventType.IMAGE_UPLOADED, f"Image uploaded for: {it['name']}", {"id": item_id, "image_id": image_id})
    return {**it, "image_id": image_id}


@router.post("/items/{item_id}/mark-sold", response_model=Item)
async def mark_sold(item_id: str, payload: MarkSoldRequest, wid: str = Depends(get_wid)):
    it = await _find_item(item_id, wid)
    now = datetime.now(timezone.utc)
    sold_at = parse_iso(payload.sold_at) if payload.sold_at else now
    update = {"sold": True, "stage": "sold", "sale_price": round(float(payload.sale_price), 2), "sold_at": sold_at.isoformat()}
    await db.items.update_one({"id": item_id, "workspace_id": wid}, {"$set": update})
    await log_event(wid, EventType.ITEM_SOLD, f"Item sold: {it['name']}",
                    {"id": item_id, "name": it["name"], "sale_price": update["sale_price"], "sold_at": update["sold_at"]})
    await notify(wid, f"Sale recorded: {it['name']}", f"Sold for {update['sale_price']} — realized P&L updated.", "sale", f"/items/{item_id}")
    return {**it, **update, "sold_at": sold_at}


@router.post("/items/{item_id}/mark-unsold", response_model=Item)
async def mark_unsold(item_id: str, wid: str = Depends(get_wid)):
    it = await _find_item(item_id, wid)
    has_listing = await db.listings.count_documents({"item_id": item_id, "workspace_id": wid})
    update = {"sold": False, "stage": "listed" if has_listing else "inventory", "sale_price": None, "sold_at": None}
    await db.items.update_one({"id": item_id, "workspace_id": wid}, {"$set": update})
    await log_event(wid, EventType.ITEM_UNSOLD, f"Sale reverted: {it['name']}", {"id": item_id, "name": it["name"]})
    return {**it, **update}
