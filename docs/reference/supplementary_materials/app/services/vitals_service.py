from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import User, Vitals, Alert


def add_vitals_service(db: Session, user_id: int, weight_value: float, spo2_value: float):
    patient = db.query(User).filter(User.id == user_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if not patient.is_active:
        raise HTTPException(status_code=403, detail="Inactive account")

    previous_vitals = (
        db.query(Vitals)
        .filter(Vitals.patient_id == user_id)
        .order_by(Vitals.recorded_at.desc())
        .first()
    )

    new_vitals = Vitals(
        patient_id=user_id,
        weight_value=weight_value,
        spo2_value=spo2_value
    )

    db.add(new_vitals)
    db.flush()

    if previous_vitals:
        weight_difference = weight_value - previous_vitals.weight_value

        if abs(weight_difference) > 2:
            db.add(Alert(
                patient_id=user_id,
                vital_id=new_vitals.id,
                alert_type="weight",
                severity="high",
                message="Clinically significant weight change detected",
                status="active"
            ))

    if spo2_value < 92:
        db.add(Alert(
            patient_id=user_id,
            vital_id=new_vitals.id,
            alert_type="spo2",
            severity="critical" if spo2_value < 88 else "high",
            message="Low oxygen saturation detected",
            status="active"
        ))

    db.commit()
    db.refresh(new_vitals)

    return new_vitals
