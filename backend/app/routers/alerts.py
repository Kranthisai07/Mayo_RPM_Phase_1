from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.auth.dependencies import require_role
from app.schemas.alert import AlertResponse
from app.services.alert_service import (
    get_user_alerts,
    get_active_alerts,
    get_alerts_by_user,
    acknowledge_alert_service,
    resolve_alert_service
)
from app.services.audit_service import log_audit

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/me", response_model=list[AlertResponse])
def get_my_alerts(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["patient"]))
):
    return get_user_alerts(db, current_user["user_id"])



@router.get("/me/active", response_model=list[AlertResponse])
def get_my_active_alerts(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["patient"]))
):
    return get_active_alerts(db, current_user["user_id"])


@router.get("/user/{user_id}", response_model=list[AlertResponse])
def get_user_alerts_route(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["patient"]))
):
    return get_alerts_by_user(db, current_user["user_id"], user_id)



@router.put("/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = acknowledge_alert_service(
        db,
        current_user["user_id"],
        current_user["role"],
        alert_id,
    )
    log_audit(
        db,
        action="ALERT_ACKNOWLEDGED",
        actor_user_id=current_user["user_id"],
        target_type="alert",
        target_id=alert_id,
        details=f"{current_user['role'].capitalize()} acknowledged alert",
    )
    return result



@router.put("/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = resolve_alert_service(
        db,
        current_user["user_id"],
        current_user["role"],
        alert_id,
    )
    log_audit(
        db,
        action="ALERT_RESOLVED",
        actor_user_id=current_user["user_id"],
        target_type="alert",
        target_id=alert_id,
        details=f"{current_user['role'].capitalize()} resolved alert",
    )
    return result
