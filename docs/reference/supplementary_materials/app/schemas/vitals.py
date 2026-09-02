from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class VitalsCreate(BaseModel):
    weight_value: float = Field(..., gt=0, lt=1000)
    spo2_value: float = Field(..., ge=70, le=100)


class VitalsResponse(BaseModel):
    id: int
    weight_value: float
    spo2_value: float
    recorded_at: Optional[datetime]

    class Config:
        from_attributes = True