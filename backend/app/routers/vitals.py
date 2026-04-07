from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.models import Patient, Vitals, Alert
from app.auth.dependencies import get_current_user
from app.schema.schema import VitalsCreate, VitalsResponse

router = APIRouter(
    prefix="/vitals",
    tags=["Vitals"]
)


# --------------------------------------------------
# Submit vitals for current logged-in patient
# --------------------------------------------------

@router.post("/", response_model=VitalsResponse)
def add_vitals(
    data: VitalsCreate,
    db: Session = Depends(get_db),
    current_user: Patient = Depends(get_current_user)
):

    patient_id = current_user.id

    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if getattr(patient, "is_active", True) is False:
        raise HTTPException(status_code=403, detail="Inactive account")

    weight_value = data.weight_value
    spo2_value = data.spo2_value

    alerts = []

    previous_vitals = (
        db.query(Vitals)
        .filter(Vitals.patient_id == patient_id)
        .order_by(Vitals.recorded_at.desc())
        .first()
    )

    new_vitals = Vitals(
        patient_id=patient_id,
        weight_value=weight_value,
        spo2_value=spo2_value
    )

    db.add(new_vitals)
    db.flush()

    # --------------------------------------------------
    # Weight Alert Detection
    # --------------------------------------------------

    if previous_vitals:

        weight_difference = weight_value - previous_vitals.weight_value

        if abs(weight_difference) > 2:

            alert = Alert(
                patient_id=patient_id,
                vital_id=new_vitals.id,
                alert_type="weight",
                severity="high",
                message="Clinically significant weight change detected",
                status="active"
            )

            db.add(alert)
            alerts.append("Weight change alert")

    # --------------------------------------------------
    # Oxygen Alert Detection
    # --------------------------------------------------

    if spo2_value < 92:

        alert = Alert(
            patient_id=patient_id,
            vital_id=new_vitals.id,
            alert_type="spo2",
            severity="critical" if spo2_value < 88 else "high",
            message="Low oxygen saturation detected",
            status="active"
        )

        db.add(alert)
        alerts.append("Low oxygen alert")

    db.commit()
    db.refresh(new_vitals)

    return new_vitals


# --------------------------------------------------
# Get vitals for current logged-in patient
# --------------------------------------------------

@router.get("/me", response_model=list[VitalsResponse])
def get_my_vitals(
    db: Session = Depends(get_db),
    current_user: Patient = Depends(get_current_user)
):

    vitals = (
        db.query(Vitals)
        .filter(Vitals.patient_id == current_user.id)
        .order_by(Vitals.recorded_at.desc())
        .all()
    )

    return vitals


# --------------------------------------------------
# Get vitals history (patient can only read own data)
# --------------------------------------------------

@router.get("/patient/{patient_id}", response_model=list[VitalsResponse])
def get_vitals_history(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: Patient = Depends(get_current_user)
):

    if current_user.id != patient_id:
        raise HTTPException(status_code=403, detail="Access denied")

    vitals = (
        db.query(Vitals)
        .filter(Vitals.patient_id == patient_id)
        .order_by(Vitals.recorded_at.desc())
        .all()
    )

    return vitals