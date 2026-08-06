"""Image object storage (Mongo-backed blob store).

Images live in their own `image_blobs` collection so item documents stay small and
under the 16MB BSON limit; thumbnails are generated server-side with Pillow. The
interface is deliberately S3-swappable (boto3 is already a declared dependency).
"""
import base64
import io
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from deps import db

logger = logging.getLogger(__name__)

THUMB_MAX = 320

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None


def _decode(data: str) -> tuple:
    if isinstance(data, str) and data.startswith("data:"):
        meta, b64 = data.split(",", 1)
        content_type = meta.split(";")[0].split(":", 1)[1] if ":" in meta else "image/jpeg"
        return base64.b64decode(b64), content_type
    return base64.b64decode(data), "image/jpeg"


def _make_thumbnail(raw: bytes) -> Optional[bytes]:
    if Image is None:
        return None
    try:
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        img.thumbnail((THUMB_MAX, THUMB_MAX))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75)
        return buf.getvalue()
    except Exception as e:
        logger.warning(f"thumbnail generation failed: {e}")
        return None


async def store_image(wid: str, data: str) -> str:
    raw, content_type = _decode(data)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("Image is too large (max 2MB). Use a smaller or compressed photo.")
    blob_id = str(uuid.uuid4())
    await db.image_blobs.insert_one({
        "id": blob_id, "workspace_id": wid, "data": raw, "content_type": content_type,
        "thumb": _make_thumbnail(raw), "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return blob_id


async def get_image(wid: str, image_id: str) -> Optional[dict]:
    blob = await db.image_blobs.find_one({"id": image_id}, {"_id": 0})
    if not blob or blob.get("workspace_id") != wid:
        return None
    return blob


def data_uri(blob: dict) -> str:
    b64 = base64.b64encode(blob["data"]).decode("ascii")
    return f"data:{blob.get('content_type', 'image/jpeg')};base64,{b64}"
