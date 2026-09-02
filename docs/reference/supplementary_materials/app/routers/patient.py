from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database.database import get_db
from app.schemas.alert import AlertResponse
from app.schemas.user import UserResponse
from app.schemas.vitals import VitalsResponse
from app.services.alert_service import get_user_alerts
from app.services.user_service import get_patient_history, get_user_profile

router = APIRouter(prefix="/patient", tags=["Patient"])


@router.get("/me", response_model=UserResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["patient"])),
):
    return get_user_profile(db, current_user["user_id"])


@router.get("/history", response_model=list[VitalsResponse])
def get_my_history(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["patient"])),
):
    return get_patient_history(db, current_user["user_id"])


@router.get("/alerts", response_model=list[AlertResponse])
def get_my_alerts(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["patient"])),
):
    return get_user_alerts(db, current_user["user_id"])
