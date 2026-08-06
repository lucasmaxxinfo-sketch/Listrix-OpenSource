from typing import Any, Dict, Optional

from pydantic import BaseModel


class VisionRequest(BaseModel):
    image: str
    item_id: Optional[str] = None
    hint: Optional[str] = None


class AssistantRequest(BaseModel):
    query: str
    item_id: Optional[str] = None
    voice: bool = False


class ModifyRequest(BaseModel):
    detail: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
