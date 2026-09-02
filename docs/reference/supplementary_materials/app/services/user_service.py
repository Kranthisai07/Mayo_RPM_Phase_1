from sqlalchemy.orm import Session
from app.models import User
from fastapi import HTTPException
from app.models import Vitals


def get_user_profile(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def get_user_by_id(db: Session, current_user_id: int, target_user_id: int):
    if current_user_id != target_user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    user = db.query(User).filter(User.id == target_user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def get_patient_history(db: Session, user_id: int):
    return (
        db.query(Vitals)
        .filter(Vitals.patient_id == user_id)
        .order_by(Vitals.recorded_at.desc())
        .all()
    )
