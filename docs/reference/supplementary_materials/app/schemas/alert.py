from pydantic import BaseModel
from typing import Optional
from datetime import datetime


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