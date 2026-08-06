import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Performance(BaseModel):
    model_config = ConfigDict(extra="ignore")
    workspace_id: str = ""
    item_id: str
    item_name: str
    status: str
    likelihood_of_sale: float
    reason: str
    recommended_action: str
    time_on_market_hours: float
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Suggestion(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str = ""
    item_id: str
    item_name: str
    listing_id: Optional[str] = None
    type: str
    title: str
    detail: str
    confidence: float
    expected_impact: str
    expected_outcome: str = ""
    risk_level: str = "low"
    reason: str
    params: Dict[str, Any] = {}
    status: str = "pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    applied_at: Optional[datetime] = None
    dismissed_at: Optional[datetime] = None


class Brief(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str = ""
    headline: str
    summary: str
    what_sold: str
    what_didnt_sell: str
    priority_items: List[str] = []
    suggested_actions: List[str] = []
    risk_alerts: List[str] = []
    opportunities: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
