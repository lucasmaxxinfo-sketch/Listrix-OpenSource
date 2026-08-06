"""In-process background job queue.

Heavy operations (analyze-all, scheduled analysis) are enqueued as persisted jobs;
workers run on the app's event loop and progress is polled via GET /api/jobs/{id}.
Swappable for a real task queue later without touching callers.
"""
import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from deps import db

logger = logging.getLogger(__name__)

WORKER_CONCURRENCY = 3
_TASKS: dict = {}  # job_id -> asyncio.Task (bookkeeping only)


async def create_job(wid: str, kind: str, total: int = 0, meta: Optional[dict] = None) -> str:
    job_id = str(uuid.uuid4())
    await db.jobs.insert_one({
        "id": job_id, "workspace_id": wid, "kind": kind, "status": "queued",
        "total": total, "done": 0, "results": 0, "error": None, "meta": meta or {},
        "created_at": datetime.now(timezone.utc).isoformat(), "finished_at": None,
    })
    return job_id


async def get_job(wid: str, job_id: str) -> Optional[dict]:
    return await db.jobs.find_one({"id": job_id, "workspace_id": wid}, {"_id": 0})


async def update_job(wid: str, job_id: str, **kw) -> None:
    kw["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.jobs.update_one({"id": job_id, "workspace_id": wid}, {"$set": kw})


def spawn(wid: str, job_id: str, coro) -> None:
    _TASKS[job_id] = asyncio.create_task(coro)


async def finish_job(wid: str, job_id: str, status: str, **kw) -> None:
    await update_job(wid, job_id, status=status, finished_at=datetime.now(timezone.utc).isoformat(), **kw)


async def run_analysis_job(wid: str, job_id: str, item_ids: list) -> None:
    """Runs the analyze-all workload for an existing job, updating progress as it goes."""
    from services.marketing_agent import analyze_one  # local import avoids a cycle

    await update_job(wid, job_id, status="running")
    sem = asyncio.Semaphore(WORKER_CONCURRENCY)
    done = 0
    results = 0

    async def safe(item_id: str):
        nonlocal done, results
        async with sem:
            item = await db.items.find_one({"id": item_id, "workspace_id": wid}, {"_id": 0})
            if not item:
                done += 1
                return
            try:
                await analyze_one(wid, item)
                results += 1
            except Exception as e:
                logger.error(f"analyze-all item failed ({item_id}): {e}")
            done += 1
            await update_job(wid, job_id, done=done, results=results)

    await asyncio.gather(*[safe(i) for i in item_ids])
    await finish_job(wid, job_id, "done", done=done, results=results)
    logger.info(f"job {job_id} finished: {results}/{done} analyzed")
