import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    password_hash: str
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    accepted_terms: bool = False
    accepted_terms_at: Optional[datetime] = None
    accepted_terms_version: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    accepted_terms: bool = False

    @field_validator("password")
    @classmethod
    def pw(cls, v):
        if not v or len(str(v)) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v



class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: EmailStr
    name: Optional[str] = None
    created_at: datetime
    accepted_terms: bool = False
    accepted_terms_at: Optional[datetime] = None
    accepted_terms_version: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
