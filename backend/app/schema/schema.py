from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# =====================================================
# Patient Schemas
# =====================================================

class PatientCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    age: int = Field(..., ge=0, le=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=256)


class PatientResponse(BaseModel):
    id: int
    name: str
    age: int
    email: EmailStr
    created_at: Optional[datetime]
    is_active: Optional[bool]
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


# =====================================================
# Authentication Schemas
# =====================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    patient_id: int
    email: EmailStr
    exp: datetime


# =====================================================
# Vitals Schemas
# =====================================================

class VitalsCreate(BaseModel):
    weight_value: float = Field(..., gt=0, lt=300)
    spo2_value: float = Field(..., ge=70, le=100)


class VitalsResponse(BaseModel):
    id: int
    weight_value: float
    spo2_value: float
    recorded_at: Optional[datetime]

    class Config:
        from_attributes = True


# =====================================================
# Alert Schemas
# =====================================================

class AlertResponse(BaseModel):
    id: int
    patient_id: int
    vital_id: Optional[int]
    alert_type: str
    severity: str
    message: str
    status: str
    created_at: Optional[datetime]

    class Config:
        from_attributes = True