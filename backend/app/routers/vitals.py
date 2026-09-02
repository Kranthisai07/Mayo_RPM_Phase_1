from app.services.weight_analysis_service import (
    get_latest_patient_weight_ai_status,
)

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.auth.dependencies import require_role
from app.schemas.vitals import VitalsCreate, VitalsResponse
from app.services.vitals_service import add_vitals_service
from app.services.audit_service import log_audit

router = APIRouter(prefix="/vitals", tags=["Vitals"])


@router.post("/", response_model=VitalsResponse)
def add_vitals(
    data: VitalsCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["patient"]))
):
    vitals = add_vitals_service(
        db,
        current_user["user_id"],
        data.weight_value,
        data.spo2_value
    )
    log_audit(
        db,
        action="PATIENT_SUBMITTED_VITALS",
        actor_user_id=current_user["user_id"],
        target_type="vitals",
        target_id=vitals.id,
        details="Patient submitted vitals",
    )
    return vitals
@router.get("/weight-ai/{patient_id}")
def get_weight_ai_status(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(["nurse", "admin"])
    ),
):
    return get_latest_patient_weight_ai_status(
        db,
        patient_id,
    )