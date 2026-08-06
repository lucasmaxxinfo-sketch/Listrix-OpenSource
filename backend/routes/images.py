from fastapi import APIRouter, Depends, HTTPException, Response

from deps import get_wid
from services.storage import get_image

router = APIRouter()


@router.get("/images/{image_id}")
async def serve_image(image_id: str, thumb: bool = False, wid: str = Depends(get_wid)):
    blob = await get_image(wid, image_id)
    if not blob:
        raise HTTPException(status_code=404, detail="Image not found")
    if thumb and blob.get("thumb"):
        return Response(content=blob["thumb"], media_type="image/jpeg")
    return Response(content=blob["data"], media_type=blob.get("content_type", "image/jpeg"))
