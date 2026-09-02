from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class NurseCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=256)


class NurseResponse(BaseModel):
    id: int
    name: str
    age: Optional[int]
    email: EmailStr
    role: str
    is_active: bool
    is_available: bool
    created_at: Optional[datetime]
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class NurseStatusUpdate(BaseModel):
    is_available: bool


class NurseDashboardResponse(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    is_available: bool
    assigned_patient_count: int
    active_alert_count: int
