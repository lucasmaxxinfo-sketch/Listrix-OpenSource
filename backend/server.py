from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware

import os
from db.indexes import ensure_indexes
from db.migrations import ensure_default_workspace
from deps import client
from services.scheduler import start_scheduler_if_enabled
from routes import agent, analytics, assistant, auth, brief, events, financials, images, inbox, integrations, items, jobs, listings, notifications, search, suggestions, vision, workspaces

app = FastAPI(title="Listrix")
api_router = APIRouter(prefix="/api")

api_router.include_router(auth.router)
api_router.include_router(workspaces.router)
api_router.include_router(items.router)
api_router.include_router(listings.router)
api_router.include_router(events.router)
api_router.include_router(financials.router)
api_router.include_router(images.router)
api_router.include_router(jobs.router)
api_router.include_router(notifications.router)
api_router.include_router(search.router)
api_router.include_router(analytics.router)
api_router.include_router(vision.router)
api_router.include_router(agent.router)
api_router.include_router(suggestions.router)
api_router.include_router(assistant.router)
api_router.include_router(brief.router)
api_router.include_router(integrations.router)
api_router.include_router(inbox.router)

app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup():
    await ensure_default_workspace()
    await ensure_indexes()
    start_scheduler_if_enabled()


@app.on_event("shutdown")
async def _shutdown():
    client.close()
