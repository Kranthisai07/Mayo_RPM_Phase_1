from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models import PatientAssignment, User
from app.services.audit_service import log_audit


def _get_active_assignment_for_patient(db: Session, patient_id: int) -> PatientAssignment | None:
    return (
        db.query(PatientAssignment)
        .filter(
            PatientAssignment.patient_id == patient_id,
            PatientAssignment.is_active.is_(True),
        )
        .first()
    )


def _deactivate_patient_assignments(db: Session, patient_id: int) -> None:
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


def _get_active_unassigned_patients(db: Session):
    return (
        db.query(User)
        .outerjoin(
            PatientAssignment,
            (PatientAssignment.patient_id == User.id)
            & (PatientAssignment.is_active.is_(True)),
        )
        .filter(
            User.role == "patient",
            User.is_active.is_(True),
            PatientAssignment.id.is_(None),
        )
        .order_by(User.created_at.asc(), User.id.asc())
        .all()
    )


def get_nurse_patient_count(db: Session, nurse_id: int) -> int:
    return (
        db.query(PatientAssignment)
        .join(User, User.id == PatientAssignment.patient_id)
        .filter(
            PatientAssignment.nurse_id == nurse_id,
            PatientAssignment.is_active.is_(True),
            User.is_active.is_(True),
            User.role == "patient",
        )
        .count()
    )


def get_nurse_assigned_patients(db: Session, nurse_id: int):
    return (
        db.query(User)
        .join(PatientAssignment, PatientAssignment.patient_id == User.id)
        .filter(
            PatientAssignment.nurse_id == nurse_id,
            PatientAssignment.is_active.is_(True),
            User.role == "patient",
            User.is_active.is_(True),
        )
        .order_by(User.created_at.asc(), User.id.asc())
        .all()
    )


def is_patient_assigned_to_nurse(db: Session, patient_id: int, nurse_id: int) -> bool:
    assignment = (
        db.query(PatientAssignment)
        .filter(
            PatientAssignment.patient_id == patient_id,
            PatientAssignment.nurse_id == nurse_id,
            PatientAssignment.is_active.is_(True),
        )
        .first()
    )
    return assignment is not None


def assign_patient_to_available_nurse(db: Session, patient_id: int):
    patient = db.query(User).filter(User.id == patient_id).first()
    if not patient or patient.role != "patient" or not patient.is_active:
        raise HTTPException(status_code=404, detail="Active patient not found")

    nurses = (
        db.query(User)
        .filter(
            User.role == "nurse",
            User.is_active.is_(True),
            User.is_available.is_(True),
        )
        .order_by(User.created_at.asc(), User.id.asc())
        .all()
    )

    if not nurses:
        return None

    selected_nurse = min(
        nurses,
        key=lambda nurse: (get_nurse_patient_count(db, nurse.id), nurse.id),
    )

    _deactivate_patient_assignments(db, patient_id)

    assignment = PatientAssignment(
        patient_id=patient_id,
        nurse_id=selected_nurse.id,
        is_active=True,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def assign_waiting_patients(db: Session):
    assignments = []
    for patient in _get_active_unassigned_patients(db):
        assignment = assign_patient_to_available_nurse(db, patient.id)
        if assignment:
            assignments.append(assignment)
    return assignments


def manually_assign_patient_to_nurse(
    db: Session,
    patient_id: int,
    nurse_id: int,
    actor_user_id: int,
):
    patient = db.query(User).filter(User.id == patient_id).first()
    if not patient or patient.role != "patient":
        raise HTTPException(status_code=404, detail="Patient not found")
    if not patient.is_active:
        raise HTTPException(status_code=400, detail="Patient is inactive")

    nurse = db.query(User).filter(User.id == nurse_id).first()
    if not nurse or nurse.role != "nurse":
        raise HTTPException(status_code=404, detail="Nurse not found")
    if not nurse.is_active:
        raise HTTPException(status_code=400, detail="Nurse is inactive")

    _deactivate_patient_assignments(db, patient_id)

    assignment = PatientAssignment(
        patient_id=patient_id,
        nurse_id=nurse_id,
        is_active=True,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    details = (
        "Patient manually assigned to nurse"
        if nurse.is_available
        else "Patient manually assigned to unavailable nurse by admin override"
    )
    log_audit(
        db,
        action="ADMIN_ASSIGNED_PATIENT",
        actor_user_id=actor_user_id,
        target_type="patient",
        target_id=patient_id,
        details=details,
    )
    return assignment


def get_active_assignments_with_details(db: Session):
    return (
        db.query(PatientAssignment)
        .options(
            joinedload(PatientAssignment.patient),
            joinedload(PatientAssignment.nurse),
        )
        .filter(PatientAssignment.is_active.is_(True))
        .order_by(PatientAssignment.assigned_at.desc(), PatientAssignment.id.desc())
        .all()
    )
