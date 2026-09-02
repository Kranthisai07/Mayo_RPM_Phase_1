from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Alert, PatientAssignment


def get_user_alerts(db: Session, user_id: int):
    return (
        db.query(Alert)
        .filter(Alert.patient_id == user_id)
        .order_by(Alert.created_at.desc())
        .all()
    )


def get_alerts_for_nurse(db: Session, nurse_id: int):
    return (
        db.query(Alert)
        .join(
            PatientAssignment,
            PatientAssignment.patient_id == Alert.patient_id,
        )
        .filter(
            PatientAssignment.nurse_id == nurse_id,
            PatientAssignment.is_active.is_(True),
        )
        .order_by(Alert.created_at.desc())
        .all()
    )


def get_active_alerts(db: Session, user_id: int):
    return (
        db.query(Alert)
        .filter(
            Alert.patient_id == user_id,
            Alert.status == "active"
        )
        .order_by(Alert.created_at.desc())
        .all()
    )


def get_active_alerts_for_nurse(db: Session, nurse_id: int):
    return (
        db.query(Alert)
        .join(
            PatientAssignment,
            PatientAssignment.patient_id == Alert.patient_id,
        )
        .filter(
            PatientAssignment.nurse_id == nurse_id,
            PatientAssignment.is_active.is_(True),
            Alert.status == "active",
        )
        .order_by(Alert.created_at.desc())
        .all()
    )


def get_alerts_by_user(db: Session, current_user_id: int, target_user_id: int):
    if current_user_id != target_user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return (
        db.query(Alert)
        .filter(Alert.patient_id == target_user_id)
        .order_by(Alert.created_at.desc())
        .all()
    )


def _can_nurse_manage_alert(db: Session, nurse_id: int, patient_id: int) -> bool:
    return (
        db.query(PatientAssignment)
        .filter(
            PatientAssignment.nurse_id == nurse_id,
            PatientAssignment.patient_id == patient_id,
            PatientAssignment.is_active.is_(True),
        )
        .first()
        is not None
    )


def _get_manageable_alert(db: Session, actor_user_id: int, actor_role: str, alert_id: int) -> Alert:
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if actor_role == "patient":
        if alert.patient_id != actor_user_id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif actor_role == "nurse":
        if not _can_nurse_manage_alert(db, actor_user_id, alert.patient_id):
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        raise HTTPException(status_code=403, detail="Access denied")

    return alert


def acknowledge_alert_service(db: Session, actor_user_id: int, actor_role: str, alert_id: int):
    alert = _get_manageable_alert(db, actor_user_id, actor_role, alert_id)

    if alert.status != "active":
        return {"message": f"Alert already {alert.status}"}

    alert.status = "acknowledged"
    db.commit()

    return {"message": "Alert acknowledged successfully"}


def resolve_alert_service(db: Session, actor_user_id: int, actor_role: str, alert_id: int):
    alert = _get_manageable_alert(db, actor_user_id, actor_role, alert_id)

    if alert.status == "resolved":
        return {"message": "Alert already resolved"}

    alert.status = "resolved"
    db.commit()

    return {"message": "Alert resolved successfully"}
