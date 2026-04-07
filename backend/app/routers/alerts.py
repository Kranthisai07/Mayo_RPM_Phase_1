from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.models import Alert, Patient, Vitals
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"]
)


# -------------------------
# Get alerts for current logged-in patient
# -------------------------
@router.get("/me")
def get_my_alerts(
    db: Session = Depends(get_db),
    current_user: Patient = Depends(get_current_user)
):
    alerts = (
        db.query(Alert)
        .filter(Alert.patient_id == current_user.id)
        .order_by(Alert.created_at.desc())
        .all()
    )

    return alerts


# -------------------------
# Get active alerts for current logged-in patient
# -------------------------
@router.get("/me/active")
def get_my_active_alerts(
    db: Session = Depends(get_db),
    current_user: Patient = Depends(get_current_user)
):
    alerts = (
        db.query(Alert)
        .filter(
            Alert.patient_id == current_user.id,
            Alert.status == "active"
        )
        .order_by(Alert.created_at.desc())
        .all()
    )

    return alerts


# -------------------------
# Get alerts by patient id
# Patient can only read their own alerts
# -------------------------
@router.get("/patient/{patient_id}")
def get_patient_alerts(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: Patient = Depends(get_current_user)
):
    if current_user.id != patient_id:
        raise HTTPException(status_code=403, detail="Access denied")

    alerts = (
        db.query(Alert)
        .filter(Alert.patient_id == patient_id)
        .order_by(Alert.created_at.desc())
        .all()
    )

    return alerts


# -------------------------
# Acknowledge alert
# For now: only allow patient to acknowledge their own alert
# Later this should move to nurse/admin RBAC
# -------------------------
@router.put("/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: Patient = Depends(get_current_user)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if alert.status != "active":
        return {"message": f"Alert already {alert.status}"}

    alert.status = "acknowledged"
    db.commit()

    return {"message": "Alert acknowledged successfully"}


# -------------------------
# Resolve alert
# For now: only allow patient to resolve their own alert
# Later this should move to nurse/admin RBAC
# -------------------------
@router.put("/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: Patient = Depends(get_current_user)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if alert.status == "resolved":
        return {"message": "Alert already resolved"}

    alert.status = "resolved"
    db.commit()

    return {"message": "Alert resolved successfully"}