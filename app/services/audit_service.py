from sqlalchemy.orm import Session
from models.models import AuditLog, AuditLogAction, User
from typing import Optional, Dict, Any

def log_action(
    db: Session,
    action: AuditLogAction,
    actor: Optional[User] = None,
    details: Optional[Dict[str, Any]] = None
):
    log_entry = AuditLog(
        user_id=actor.id if actor else None,
        action=action,
        details=details if details else {}
    )
    db.add(log_entry)
    db.commit()