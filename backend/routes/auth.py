from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

import config
from deps import db, get_current_user
from models import LoginRequest, TokenResponse, User, UserCreate, UserOut, Workspace
from services.auth import create_token, hash_password, verify_password
from services.events import EventType, log_event
from utils import parse_iso

router = APIRouter()


def _user_out(user: dict) -> UserOut:
    return UserOut(
        id=user["id"],
        email=user["email"],
        name=user.get("name"),
        created_at=parse_iso(user.get("created_at")),
        accepted_terms=bool(user.get("accepted_terms", False)),
        accepted_terms_at=parse_iso(user.get("accepted_terms_at")) if user.get("accepted_terms_at") else None,
        accepted_terms_version=user.get("accepted_terms_version"),
    )


@router.post("/auth/register", response_model=TokenResponse)
async def register(payload: UserCreate):
    email = str(payload.email).lower().strip()
    exists = await db.users.find_one({"email": email}, {"_id": 0, "id": 1})
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")
    if not payload.accepted_terms:
        raise HTTPException(status_code=400, detail="You must accept the Terms and Privacy Policy to create an account")
    now = datetime.now(timezone.utc)
    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        accepted_terms=True,
        accepted_terms_at=now,
        accepted_terms_version=config.TERMS_VERSION,
    )
    doc = user.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.users.insert_one({**doc})
    # each user gets an owned default workspace + seeded connectors
    ws = Workspace(name=payload.name or "My Business", is_default=True, owner_id=user.id)
    wdoc = ws.model_dump()
    wdoc["created_at"] = wdoc["created_at"].isoformat()
    await db.workspaces.insert_one({**wdoc})
    for c in config.DEFAULT_CONNECTORS:
        await db.integrations.insert_one({**c, "workspace_id": ws.id, "last_sync": None})
    await log_event(ws.id, EventType.WORKSPACE_CREATED, f"Workspace created: {ws.name}", {"workspace": ws.name, "owner": user.id})
    await log_event(ws.id, EventType.AUTH_USER_REGISTERED, f"User registered: {email}", {"user_id": user.id})
    await log_event(
        ws.id,
        EventType.USER_CONSENT,
        f"User accepted Terms & Privacy v{config.TERMS_VERSION}: {email}",
        {"user_id": user.id, "terms_version": config.TERMS_VERSION, "accepted_at": now.isoformat()},
    )
    return TokenResponse(access_token=create_token(user.id), user=_user_out(doc))


@router.post("/auth/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    email = str(payload.email).lower().strip()
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    owned = await db.workspaces.find_one({"owner_id": user["id"]}, {"_id": 0, "id": 1})
    if owned:
        await log_event(owned["id"], EventType.AUTH_LOGIN, f"User logged in: {email}", {"user_id": user["id"]})
    return TokenResponse(access_token=create_token(user["id"]), user=_user_out(user))


@router.get("/auth/me", response_model=UserOut)
async def me(user: dict = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return _user_out(user)
