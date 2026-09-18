from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import User, Vitals, Alert
from app.services.weight_analysis_service import get_latest_patient_weight_ai_status


AI_WEIGHT_ALERT_TYPE = "ai_weight_anomaly"


def _has_active_ai_weight_alert(db: Session, patient_id: int) -> bool:
    return (
        db.query(Alert)
        .filter(
            Alert.patient_id == patient_id,
            Alert.alert_type == AI_WEIGHT_ALERT_TYPE,
            Alert.status != "resolved",
        )
        .first()
        is not None
    )


def _maybe_create_ai_weight_alert(db: Session, patient_id: int, vital_id: int):
    """
    Hook the AI weight-anomaly model into the same alert-creation path
    as the rule-based checks. Deliberately conservative:
      - only the model's "high" tier creates an Alert ("watch" stays a
        dashboard-only signal, to avoid alert fatigue from a model
        trained on a small real-data sample)
      - only when the AI's assessment is for the reading just submitted
        (ai_analysis_is_current), not a stale prior day
      - skipped if the patient already has an unresolved AI alert, to
        avoid near-duplicates from multiple same-day submissions
    """
    status = get_latest_patient_weight_ai_status(db, patient_id)

    if status.get("status") != "ok":
        return None

    if not status.get("ai_analysis_is_current"):
        return None

    analysis = status.get("ai_analysis") or {}

    if analysis.get("monitoring_status") != "high":
        return None

    if _has_active_ai_weight_alert(db, patient_id):
        return None

    alert = Alert(
        patient_id=patient_id,
        vital_id=vital_id,
        alert_type=AI_WEIGHT_ALERT_TYPE,
        severity="high",
        message=analysis.get("reason_text") or "AI-detected weight anomaly",
        status="active",
        ai_score=analysis.get("anomaly_score"),
    )
    db.add(alert)
    return alert


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

        if weight_difference > 1.5:
            db.add(Alert(
                patient_id=user_id,
                vital_id=new_vitals.id,
                alert_type="weight",
                severity="high",
                message=f"Weight increased by {weight_difference:.1f} kg",
                status="active"
            ))
        elif weight_difference < -2:
            db.add(Alert(
                patient_id=user_id,
                vital_id=new_vitals.id,
                alert_type="weight",
                severity="high",
                message=f"Weight decreased by {abs(weight_difference):.1f} kg",
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

    _maybe_create_ai_weight_alert(db, user_id, new_vitals.id)

    db.commit()
    db.refresh(new_vitals)

    return new_vitals
