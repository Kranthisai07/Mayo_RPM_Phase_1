from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=256)


class UserResponse(BaseModel):
    id: int
    name: str
    age: Optional[int]
    email: EmailStr
    role: str
    created_at: Optional[datetime]
    is_active: Optional[bool]
    is_available: Optional[bool]
    last_login: Optional[datetime]

    class Config:
        from_attributes = True
