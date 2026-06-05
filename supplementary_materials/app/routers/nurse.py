from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database.database import get_db
from app.models import Alert, User, Vitals
from app.schemas.alert import AlertResponse
from app.schemas.nurse import NurseDashboardResponse, NurseResponse, NurseStatusUpdate
from app.schemas.patient import PatientResponse
from app.schemas.vitals import VitalsResponse
from app.services.alert_service import get_alerts_for_nurse
from app.services.assignment_service import (
    assign_waiting_patients,
    get_nurse_assigned_patients,
    get_nurse_patient_count,
    is_patient_assigned_to_nurse,
)
from app.services.audit_service import log_audit

router = APIRouter(prefix="/nurse", tags=["Nurse"])


@router.get("/dashboard", response_model=NurseDashboardResponse)
def get_nurse_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["nurse"])),
):
    nurse = db.query(User).filter(User.id == current_user["user_id"]).first()
    nurse_alerts = get_alerts_for_nurse(db, nurse.id)
    return {
        "user_id": nurse.id,
        "name": nurse.name,
        "email": nurse.email,
        "is_available": nurse.is_available,
        "assigned_patient_count": get_nurse_patient_count(db, nurse.id),
        "active_alert_count": len([alert for alert in nurse_alerts if alert.status == "active"]),
    }


@router.patch("/status", response_model=NurseResponse)
def update_nurse_status(
    data: NurseStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["nurse"])),
):
    nurse = db.query(User).filter(User.id == current_user["user_id"]).first()
    nurse.is_available = data.is_available
    db.commit()
    db.refresh(nurse)

    auto_assigned_count = 0
    if data.is_available:
        auto_assigned_count = len(assign_waiting_patients(db))

    log_audit(
        db,
        action="NURSE_CHANGED_STATUS",
        actor_user_id=nurse.id,
        target_type="nurse",
        target_id=nurse.id,
        details=(
            f"Availability changed to {data.is_available}; "
            f"auto-assigned waiting patients: {auto_assigned_count}"
        ),
    )
    return nurse


@router.get("/patients", response_model=list[PatientResponse])
def get_assigned_patients(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["nurse"])),
):
    return get_nurse_assigned_patients(db, current_user["user_id"])


@router.get("/patients/{patient_id}")
def get_assigned_patient_detail(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["nurse"])),
):
    nurse_id = current_user["user_id"]
    if not is_patient_assigned_to_nurse(db, patient_id, nurse_id):
        raise HTTPException(status_code=403, detail="Access denied")

    patient = db.query(User).filter(User.id == patient_id, User.role == "patient").first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    vitals_history = (
        db.query(Vitals)
        .filter(Vitals.patient_id == patient_id)
        .order_by(Vitals.recorded_at.desc())
        .all()
    )
    active_alerts = (
        db.query(Alert)
        .filter(Alert.patient_id == patient_id, Alert.status == "active")
        .order_by(Alert.created_at.desc())
        .all()
    )

    log_audit(
        db,
        action="NURSE_VIEWED_PATIENT",
        actor_user_id=nurse_id,
        target_type="patient",
        target_id=patient_id,
        details="Nurse viewed assigned patient detail",
    )

    return {
        "patient": PatientResponse.model_validate(patient),
        "recent_vitals": [VitalsResponse.model_validate(vital) for vital in vitals_history],
        "active_alerts": [AlertResponse.model_validate(alert) for alert in active_alerts],
    }


@router.get("/alerts", response_model=list[AlertResponse])
def get_assigned_alerts(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["nurse"])),
):
    return get_alerts_for_nurse(db, current_user["user_id"])
