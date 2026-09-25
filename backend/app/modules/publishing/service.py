from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.enums import PublishStatus, SessionStatus
from app.common.exceptions import ValidationFailedError
from app.modules.audit import service as audit_service
from app.modules.matches.service import get_session
from app.modules.publishing.models import MessageTemplate, PublishLog
from app.modules.publishing.publishers import MessagePublisher, NullMessagePublisher
from app.modules.publishing.schemas import PublishResultOut
from app.modules.publishing.templates import DEFAULT_TEMPLATE, render_message
from app.modules.teams.service import get_board


def _default_template_content(db: Session) -> str:
    template = db.scalar(select(MessageTemplate).where(MessageTemplate.is_default.is_(True)))
    return template.content if template else DEFAULT_TEMPLATE


def preview_message(db: Session, session_id: str) -> str:
    session = get_session(db, session_id)
    board = get_board(db, session_id)
    if not board.teams:
        raise ValidationFailedError("Chưa có đội để publish — vui lòng Generate và Finalize trước.")
    return render_message(session, board, _default_template_content(db))


def publish(db: Session, session_id: str, publisher: MessagePublisher | None = None) -> PublishResultOut:
    session = get_session(db, session_id)
    if session.status not in (SessionStatus.FINALIZED, SessionStatus.PUBLISHED):
        raise ValidationFailedError(
            "Chỉ có thể Publish sau khi đã Finalize (spec #48: FINALIZED → Generate Message → Preview → Publish)."
        )

    message = preview_message(db, session_id)
    publisher = publisher or NullMessagePublisher()

    attempt = (
        db.scalar(select(func.count(PublishLog.id)).where(PublishLog.session_id == session_id)) or 0
    ) + 1

    outcome = publisher.send_message(message)

    log = PublishLog(
        session_id=session_id,
        message_content=message,
        status=PublishStatus.SUCCESS if outcome.success else PublishStatus.FAILED,
        error=outcome.error,
        attempt=attempt,
    )
    db.add(log)

    if outcome.success:
        session.status = SessionStatus.PUBLISHED

    audit_service.record(
        db,
        session_id=session_id,
        action="PUBLISH",
        payload={"success": outcome.success, "attempt": attempt, "error": outcome.error},
    )
    db.commit()

    return PublishResultOut(
        success=outcome.success,
        message=message,
        error=outcome.error,
        attempt=attempt,
        session_status=session.status.value,
    )


def list_publish_logs(db: Session, session_id: str) -> list[PublishLog]:
    return list(
        db.scalars(
            select(PublishLog).where(PublishLog.session_id == session_id).order_by(PublishLog.attempt)
        )
    )
