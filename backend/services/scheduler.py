"""Optional periodic background work (opt-in via SCHEDULER_ENABLED=true).

Runs a tick every SCHEDULER_INTERVAL_MINUTES that enqueues analyze-all jobs for
workspaces with items. Defaults to OFF so tests and local dev are deterministic.
"""
import asyncio
import logging
from datetime import datetime, timezone

import config
from deps import db
from services.jobs import create_job, run_analysis_job, spawn

logger = logging.getLogger(__name__)

_tick_task = None


async def run_scheduled_tick() -> int:
    """One scheduled pass: enqueue analysis for every workspace that has items. Returns jobs created."""
    jobs = 0
    ws_ids = await db.workspaces.distinct("id")
    for wid in ws_ids:
        count = await db.items.count_documents({"workspace_id": wid})
        if count == 0:
            continue
        job_id = await create_job(wid, "scheduled-analyze", total=min(count, 12))
        items = await db.items.find({"workspace_id": wid}, {"_id": 0, "id": 1}).sort("created_at", -1).to_list(12)
        spawn(wid, job_id, run_analysis_job(wid, job_id, [it["id"] for it in items]))
        jobs += 1
    if jobs:
        logger.info(f"scheduled tick: queued {jobs} analysis job(s)")
    return jobs


async def _loop():
    interval = max(1, int(config.SCHEDULER_INTERVAL_MINUTES)) * 60
    while True:
        try:
            await run_scheduled_tick()
        except Exception as e:
            logger.error(f"scheduled tick failed: {e}")
        await asyncio.sleep(interval)


def start_scheduler_if_enabled():
    global _tick_task
    if not config.SCHEDULER_ENABLED:
        return
    if _tick_task is None or _tick_task.done():
        _tick_task = asyncio.create_task(_loop())
        logger.info("scheduler started")
