from typing import List

from fastapi import APIRouter, Depends, HTTPException

from config import CLIENT_EVENT_TYPES
from deps import db, get_wid
from models import ClientEvent, Event
from services.events import log_event
from utils import parse_iso

router = APIRouter()


@router.get("/events", response_model=List[Event])
async def get_events(wid: str = Depends(get_wid), limit: int = 100):
    rows = await db.events.find({"workspace_id": wid}, {"_id": 0}).sort("created_at", -1).to_list(limit)
    for ev in rows:
        ev["created_at"] = parse_iso(ev.get("created_at"))
    return rows


@router.post("/client-events")
async def create_client_event(payload: ClientEvent, wid: str = Depends(get_wid)):
    if payload.type not in CLIENT_EVENT_TYPES:
        raise HTTPException(status_code=400, detail="Event type not allowed")
    await log_event(wid, payload.type, payload.message, payload.payload)
    return {"status": "ok"}
