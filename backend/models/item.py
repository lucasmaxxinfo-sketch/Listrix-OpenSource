import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_INLINE_IMAGE_CHARS = 2_000_000


class ItemCreate(BaseModel):
    name: str
    description: str
    condition: str
    image: Optional[str] = None
    cost: Optional[float] = None
    category: Optional[str] = None
    vision: Optional[Dict[str, Any]] = None
    value_estimate: Optional[Dict[str, Any]] = None

    @field_validator("name", "description", "condition")
    @classmethod
    def nb(cls, v):
        if not v or not str(v).strip():
            raise ValueError("Field must not be empty")
        return str(v).strip()

    @field_validator("cost")
    @classmethod
    def cnn(cls, v):
        if v is not None and v < 0:
            raise ValueError("cost must be >= 0")
        return v

    @field_validator("image")
    @classmethod
    def image_size(cls, v):
        if v and len(v) > MAX_INLINE_IMAGE_CHARS:
            raise ValueError("image is too large (max ~1.5MB). Use a smaller or compressed photo.")
        return v


class Item(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str = ""
    name: str
    description: str
    condition: str
    image: Optional[str] = None
    image_id: Optional[str] = None
    cost: Optional[float] = None
    category: Optional[str] = None
    vision: Optional[Dict[str, Any]] = None
    value_estimate: Optional[Dict[str, Any]] = None
    listed_at: Optional[datetime] = None
    times_relisted: int = 0
    stage: str = "inventory"  # inventory | listed | sold | archived
    sold: bool = False
    sold_at: Optional[datetime] = None
    sale_price: Optional[float] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GenerateRequest(BaseModel):
    name: str
    description: str
    condition: str
    cost: Optional[float] = None
    item_id: Optional[str] = None

    @field_validator("name", "description", "condition")
    @classmethod
    def nb(cls, v):
        if not v or not str(v).strip():
            raise ValueError("Field must not be empty")
        return str(v).strip()


class Listing(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str = ""
    item_id: Optional[str] = None
    source_name: str
    listing_title: str
    listing_description: str
    suggested_price: float
    hashtags: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
