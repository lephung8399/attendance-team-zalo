from sqlalchemy.orm import Session

from app.modules.audit.models import AuditLog


def record(db: Session, *, session_id: str, action: str, payload: dict | None = None, performed_by: str = "admin") -> AuditLog:
    entry = AuditLog(session_id=session_id, action=action, payload=payload or {}, performed_by=performed_by)
    db.add(entry)
    db.flush()
    return entry
