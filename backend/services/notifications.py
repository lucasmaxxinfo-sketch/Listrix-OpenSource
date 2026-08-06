"""In-app notifications (bell feed). Keep it lightweight: one doc per notification."""
import logging
import uuid
from datetime import datetime, timezone

from deps import db

logger = logging.getLogger(__name__)


async def notify(wid: str, title: str, body: str = "", kind: str = "info", link: str = "") -> None:
    try:
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()), "workspace_id": wid, "title": title, "body": body,
            "kind": kind, "link": link, "read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        logger.error(f"notify failed: {e}")
