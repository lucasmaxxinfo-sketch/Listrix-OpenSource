import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class Event(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str = ""
    type: str
    message: str
    payload: Optional[Any] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ClientEvent(BaseModel):
    type: str
    message: str
    payload: Optional[Any] = None
