from fastapi import APIRouter, Depends

from deps import get_wid
from services.financials import compute_financials

router = APIRouter()


@router.get("/financials")
async def get_financials(wid: str = Depends(get_wid)):
    return await compute_financials(wid)
