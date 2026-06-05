from pydantic import BaseModel


class AdminDashboardResponse(BaseModel):
    total_patients: int
    active_patients: int
    total_nurses: int
    active_nurses: int
    available_nurses: int
    active_alerts: int
