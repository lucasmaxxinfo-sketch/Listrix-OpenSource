import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Workspace(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    logo: Optional[str] = None
    primary_color: str = "#FF7A1A"
    secondary_color: str = "#3B82F6"
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    marketplace_accounts: List[str] = []
    tax_rate: Optional[float] = None
    currency: str = "USD"
    timezone: str = "UTC"
    business_type: str = "Reseller"
    ai_preferences: Dict[str, Any] = Field(default_factory=lambda: {
        "writing_style": "persuasive and concise",
        "pricing_behavior": "competitive",
        "selling_strategy": "fast turnover",
        "customer_comms_style": "friendly and professional",
    })
    ai_memory: Dict[str, Any] = {}
    owner_id: Optional[str] = None
    is_default: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    logo: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    marketplace_accounts: Optional[List[str]] = None
    tax_rate: Optional[float] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None
    business_type: Optional[str] = None
    ai_preferences: Optional[Dict[str, Any]] = None
