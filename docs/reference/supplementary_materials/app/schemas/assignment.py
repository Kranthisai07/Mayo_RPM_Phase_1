from datetime import datetime

from pydantic import BaseModel


class AssignmentResponse(BaseModel):
    id: int
    patient_id: int
    nurse_id: int
    assigned_at: datetime | None
    is_active: bool
    patient_name: str | None = None
    patient_email: str | None = None
    nurse_name: str | None = None
    nurse_email: str | None = None

    class Config:
        from_attributes = True


class ManualAssignmentRequest(BaseModel):
    nurse_id: int
