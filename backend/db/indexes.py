"""MongoDB index definitions. ensure_indexes() is invoked on startup (server.py)."""
import logging

logger = logging.getLogger(__name__)

INDEXES = {
    "items": [{"workspace_id": 1, "created_at": -1}],
    "listings": [
        {"workspace_id": 1, "item_id": 1},
        {"workspace_id": 1, "created_at": -1},
    ],
    "events": [{"workspace_id": 1, "created_at": -1}],
    "suggestions": [
        {"workspace_id": 1, "status": 1, "confidence": -1},
        {"workspace_id": 1, "item_id": 1},
    ],
    "performance": [{"workspace_id": 1, "item_id": 1}],
    "price_history": [{"workspace_id": 1, "item_id": 1, "created_at": -1}],
    "integrations": [{"workspace_id": 1, "platform": 1}],
    "inbox": [{"workspace_id": 1, "priority": 1}],
    "image_blobs": [{"id": 1}, {"workspace_id": 1}],
    "notifications": [{"workspace_id": 1, "read": 1, "created_at": -1}],
    "jobs": [{"workspace_id": 1, "created_at": -1}],
    "workspaces": [{"id": 1}, {"is_default": 1}, {"owner_id": 1}],
    "users": [{"email": 1}],
}


async def ensure_indexes():
    from deps import db  # local import keeps this module import-order independent

    for collection, specs in INDEXES.items():
        try:
            for spec in specs:
                await db[collection].create_index([(k, int(v)) for k, v in spec.items()])
        except Exception as e:  # never block boot on index problems
            logger.warning(f"ensure_indexes failed for {collection}: {e}")
