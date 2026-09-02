from sqlalchemy.orm import Session

from app.models import AuditLog


def log_audit(
    db: Session,
    action: str,
    actor_user_id: int | None = None,
    target_type: str | None = None,
    target_id: int | None = None,
    details: str | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log
