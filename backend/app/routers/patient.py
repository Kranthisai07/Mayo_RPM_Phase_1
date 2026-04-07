from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.models import Patient
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/patient",
    tags=["Patient"]
)


# -------------------------
# Get current logged-in patient profile
# -------------------------
@router.get("/me")
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: Patient = Depends(get_current_user)
):
    patient = db.query(Patient).filter(Patient.id == current_user.id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return {
        "id": patient.id,
        "name": patient.name,
        "age": patient.age,
        "email": patient.email,
        "created_at": patient.created_at,
        "is_active": getattr(patient, "is_active", True),
        "last_login": getattr(patient, "last_login", None),
    }


# -------------------------
# Optional: Get patient by id
# Keep disabled for patient app to avoid cross-patient exposure
# -------------------------
@router.get("/{patient_id}")
def get_patient_by_id(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: Patient = Depends(get_current_user)
):
    # Minimum-necessary approach:
    # A patient should only be able to read their own record.
    if current_user.id != patient_id:
        raise HTTPException(status_code=403, detail="Access denied")

    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return {
        "id": patient.id,
        "name": patient.name,
        "age": patient.age,
        "email": patient.email,
        "created_at": patient.created_at,
        "is_active": getattr(patient, "is_active", True),
        "last_login": getattr(patient, "last_login", None),
    }