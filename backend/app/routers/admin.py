from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.auth.service import create_user, register_patient
from app.database.database import get_db
from app.models import Alert, PatientAssignment, User
from app.schemas.admin import AdminDashboardResponse
from app.schemas.alert import AlertResponse
from app.schemas.assignment import AssignmentResponse, ManualAssignmentRequest
from app.schemas.nurse import NurseCreate, NurseResponse
from app.schemas.patient import PatientCreate, PatientResponse
from app.services.assignment_service import (
    assign_patient_to_available_nurse,
    get_active_assignments_with_details,
    manually_assign_patient_to_nurse,
)
from app.services.audit_service import log_audit

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_role(["admin"]))],
)


@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_admin_dashboard(db: Session = Depends(get_db)):
    return {
        "total_patients": db.query(User).filter(User.role == "patient").count(),
        "active_patients": db.query(User).filter(User.role == "patient", User.is_active.is_(True)).count(),
        "total_nurses": db.query(User).filter(User.role == "nurse").count(),
        "active_nurses": db.query(User).filter(User.role == "nurse", User.is_active.is_(True)).count(),
        "available_nurses": db.query(User).filter(
            User.role == "nurse",
            User.is_active.is_(True),
            User.is_available.is_(True),
        ).count(),
        "active_alerts": db.query(Alert).filter(Alert.status == "active").count(),
    }


@router.post("/nurses", response_model=NurseResponse)
def create_nurse(
    data: NurseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin"])),
):
    nurse = create_user(
        db,
        name=data.name,
        age=data.age,
        email=data.email,
        password=data.password,
        role="nurse",
        is_active=True,
        is_available=False,
    )
    log_audit(
        db,
        action="ADMIN_CREATED_NURSE",
        actor_user_id=current_user["user_id"],
        target_type="nurse",
        target_id=nurse.id,
        details="Admin created nurse account",
    )
    return nurse


@router.get("/nurses", response_model=list[NurseResponse])
def list_nurses(db: Session = Depends(get_db)):
    return db.query(User).filter(User.role == "nurse").order_by(User.id.asc()).all()


@router.delete("/nurses/{nurse_id}")
def deactivate_nurse(
    nurse_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin"])),
):
    nurse = db.query(User).filter(User.id == nurse_id, User.role == "nurse").first()
    if not nurse:
        raise HTTPException(status_code=404, detail="Nurse not found")

    nurse.is_active = False
    nurse.is_available = False

    active_assignments = (
        db.query(PatientAssignment)
        .filter(
            PatientAssignment.nurse_id == nurse_id,
            PatientAssignment.is_active.is_(True),
        )
        .all()
    )

    patient_ids = [assignment.patient_id for assignment in active_assignments]
    for assignment in active_assignments:
        assignment.is_active = False

    db.commit()

    for patient_id in patient_ids:
        patient = db.query(User).filter(User.id == patient_id).first()
        if patient and patient.is_active:
            assign_patient_to_available_nurse(db, patient_id)

    log_audit(
        db,
        action="ADMIN_DEACTIVATED_NURSE",
        actor_user_id=current_user["user_id"],
        target_type="nurse",
        target_id=nurse.id,
        details="Admin deactivated nurse account",
    )
    return {"message": "Nurse deactivated successfully"}


@router.post("/patients", response_model=PatientResponse)
def create_patient(
    data: PatientCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin"])),
):
    patient = register_patient(db, data)
    log_audit(
        db,
        action="ADMIN_CREATED_PATIENT",
        actor_user_id=current_user["user_id"],
        target_type="patient",
        target_id=patient.id,
        details="Admin created patient account",
    )
    return patient


@router.get("/patients", response_model=list[PatientResponse])
def list_patients(db: Session = Depends(get_db)):
    return db.query(User).filter(User.role == "patient").order_by(User.id.asc()).all()


@router.delete("/patients/{patient_id}")
def deactivate_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin"])),
):
    patient = db.query(User).filter(User.id == patient_id, User.role == "patient").first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient.is_active = False
    active_assignments = (
        db.query(PatientAssignment)
        .filter(
            PatientAssignment.patient_id == patient_id,
            PatientAssignment.is_active.is_(True),
        )
        .all()
    )
    for assignment in active_assignments:
        assignment.is_active = False
    db.commit()

    log_audit(
        db,
        action="ADMIN_DEACTIVATED_PATIENT",
        actor_user_id=current_user["user_id"],
        target_type="patient",
        target_id=patient.id,
        details="Admin deactivated patient account",
    )
    return {"message": "Patient deactivated successfully"}


@router.get("/assignments", response_model=list[AssignmentResponse])
def list_assignments(db: Session = Depends(get_db)):
    assignments = get_active_assignments_with_details(db)
    return [
        AssignmentResponse(
            id=assignment.id,
            patient_id=assignment.patient_id,
            nurse_id=assignment.nurse_id,
            assigned_at=assignment.assigned_at,
            is_active=assignment.is_active,
            patient_name=assignment.patient.name if assignment.patient else None,
            patient_email=assignment.patient.email if assignment.patient else None,
            nurse_name=assignment.nurse.name if assignment.nurse else None,
            nurse_email=assignment.nurse.email if assignment.nurse else None,
        )
        for assignment in assignments
    ]


@router.get("/alerts", response_model=list[AlertResponse])
def list_all_alerts(db: Session = Depends(get_db)):
    return db.query(Alert).order_by(Alert.created_at.desc()).all()


@router.patch("/patients/{patient_id}/assign-nurse", response_model=AssignmentResponse)
def assign_nurse_to_patient(
    patient_id: int,
    data: ManualAssignmentRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin"])),
):
    assignment = manually_assign_patient_to_nurse(
        db,
        patient_id=patient_id,
        nurse_id=data.nurse_id,
        actor_user_id=current_user["user_id"],
    )
    patient = db.query(User).filter(User.id == assignment.patient_id).first()
    nurse = db.query(User).filter(User.id == assignment.nurse_id).first()
    return AssignmentResponse(
        id=assignment.id,
        patient_id=assignment.patient_id,
        nurse_id=assignment.nurse_id,
        assigned_at=assignment.assigned_at,
        is_active=assignment.is_active,
        patient_name=patient.name if patient else None,
        patient_email=patient.email if patient else None,
        nurse_name=nurse.name if nurse else None,
        nurse_email=nurse.email if nurse else None,
    )
