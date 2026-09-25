from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.enums import AttendanceStatus, SessionStatus
from app.common.exceptions import NotFoundError, ValidationFailedError
from app.modules.matches.models import MatchSession
from app.modules.matches.schemas import MatchSessionCreate, MatchSessionUpdate, TeamConfigurationUpdate
from app.modules.matches.suggestion import validate_configuration


def list_sessions(db: Session) -> list[dict]:
    from app.modules.attendance.models import SessionParticipant

    sessions = list(db.scalars(select(MatchSession).order_by(MatchSession.play_date.desc())))
    counts = dict(
        db.execute(
            select(SessionParticipant.session_id, func.count(SessionParticipant.id))
            .where(SessionParticipant.attendance_status != AttendanceStatus.CANCELLED)
            .group_by(SessionParticipant.session_id)
        ).all()
    )
    return [{**s.__dict__, "participant_count": counts.get(s.id, 0)} for s in sessions]


def get_session(db: Session, session_id: str) -> MatchSession:
    session = db.get(MatchSession, session_id)
    if session is None:
        raise NotFoundError(f"Match session {session_id} not found")
    return session


def create_session(db: Session, data: MatchSessionCreate) -> MatchSession:
    session = MatchSession(
        title=data.title,
        play_date=data.play_date,
        start_time=data.start_time,
        location=data.location,
        zalo_group_id=data.zalo_group_id,
        status=SessionStatus.OPEN,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def update_session(db: Session, session_id: str, data: MatchSessionUpdate) -> MatchSession:
    session = get_session(db, session_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(session, field, value)
    db.commit()
    db.refresh(session)
    return session


def count_active_participants(db: Session, session_id: str) -> int:
    from app.modules.attendance.models import SessionParticipant

    return db.scalar(
        select(func.count(SessionParticipant.id)).where(
            SessionParticipant.session_id == session_id,
            SessionParticipant.attendance_status != AttendanceStatus.CANCELLED,
        )
    ) or 0


def update_configuration(db: Session, session_id: str, data: TeamConfigurationUpdate) -> MatchSession:
    session = get_session(db, session_id)
    participant_count = count_active_participants(db, session_id)
    issues = validate_configuration(
        team_count=data.team_count,
        player_per_team=data.player_per_team,
        substitute_count=data.substitute_count,
        participant_count=participant_count,
    )
    if issues:
        raise ValidationFailedError(issues[0], issues)

    session.team_count = data.team_count
    session.player_per_team = data.player_per_team
    session.substitute_count = data.substitute_count
    if session.status == SessionStatus.OPEN:
        session.status = SessionStatus.LOCKED
    db.commit()
    db.refresh(session)
    return session
