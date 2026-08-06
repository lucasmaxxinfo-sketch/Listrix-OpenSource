from fastapi import APIRouter, Depends, HTTPException

from deps import get_wid
from services.jobs import get_job

router = APIRouter()


@router.get("/jobs/{job_id}")
async def job_status(job_id: str, wid: str = Depends(get_wid)):
    job = await get_job(wid, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
