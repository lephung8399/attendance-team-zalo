from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.enums import (
    AttendanceSource,
    AttendanceStatus,
    ParticipantType,
    SessionStatus,
    SkillLevel,
)
from app.common.exceptions import NotFoundError, ValidationFailedError
from app.common.skill import default_score_for
from app.modules.attendance.models import SessionParticipant
from app.modules.attendance.providers import AttendanceProvider
from app.modules.attendance.schemas import AddGuestRequest, UpdateParticipantRequest
from app.modules.audit import service as audit_service
from app.modules.matches.service import get_session
from app.modules.members.models import Member


def list_participants(db: Session, session_id: str) -> list[SessionParticipant]:
    stmt = (
        select(SessionParticipant)
        .where(SessionParticipant.session_id == session_id)
        .order_by(SessionParticipant.created_at)
    )
    return list(db.scalars(stmt))


def _get_participant(db: Session, session_id: str, participant_id: str) -> SessionParticipant:
    participant = db.get(SessionParticipant, participant_id)
    if participant is None or participant.session_id != session_id:
        raise NotFoundError(f"Participant {participant_id} not found in session {session_id}")
    return participant


def _ensure_editable(session_status: SessionStatus) -> None:
    if session_status in (SessionStatus.FINALIZED, SessionStatus.PUBLISHED):
        raise ValidationFailedError(
            "Buổi đá đã Finalize. Vui lòng Re-open Session trước khi chỉnh sửa danh sách (BR-05)."
        )


def sync_attendance(db: Session, session_id: str, provider: AttendanceProvider) -> list[SessionParticipant]:
    """Idempotent sync keyed by (session_id, member_id) — spec #63 Idempotency."""
    session = get_session(db, session_id)
    existing_by_member = {
        p.member_id: p
        for p in list_participants(db, session_id)
        if p.member_id is not None
    }
    results: list[SessionParticipant] = []
    for item in provider.get_participants():
        if item.member_id in existing_by_member:
            results.append(existing_by_member[item.member_id])
            continue
        skill_level = item.skill_level or SkillLevel.UNKNOWN
        participant = SessionParticipant(
            session_id=session_id,
            member_id=item.member_id,
            participant_name=item.display_name,
            participant_type=ParticipantType.MEMBER,
            skill_level=skill_level,
            skill_score=default_score_for(skill_level),
            attendance_source=AttendanceSource.MANUAL,
            attendance_status=AttendanceStatus.CONFIRMED,
        )
        db.add(participant)
        results.append(participant)
    db.commit()
    audit_service.record(
        db, session_id=session_id, action="SYNC_ATTENDANCE", payload={"count": len(results)}
    )
    db.commit()
    for p in results:
        db.refresh(p)
    return results


def add_member_participant(db: Session, session_id: str, member_id: str, skill_override: SkillLevel | None) -> SessionParticipant:
    session = get_session(db, session_id)
    _ensure_editable(session.status)
    member = db.get(Member, member_id)
    if member is None:
        raise NotFoundError(f"Member {member_id} not found")

    already = db.scalar(
        select(SessionParticipant).where(
            SessionParticipant.session_id == session_id, SessionParticipant.member_id == member_id
        )
    )
    if already is not None:
        raise ValidationFailedError("Thành viên này đã có trong danh sách buổi đá (BR-02).")

    skill_level = skill_override or member.skill_level
    skill_score = member.skill_score if skill_override is None else default_score_for(skill_override)
    participant = SessionParticipant(
        session_id=session_id,
        member_id=member.id,
        participant_name=member.display_name,
        participant_type=ParticipantType.MEMBER,
        skill_level=skill_level,
        skill_score=skill_score,
        attendance_source=AttendanceSource.MANUAL,
        attendance_status=AttendanceStatus.CONFIRMED,
    )
    db.add(participant)
    audit_service.record(
        db, session_id=session_id, action="ADD_MEMBER", payload={"member_id": member_id}
    )
    db.commit()
    db.refresh(participant)
    return participant


def add_guest(db: Session, session_id: str, data: AddGuestRequest) -> SessionParticipant:
    session = get_session(db, session_id)
    _ensure_editable(session.status)

    next_seq = (
        db.scalar(
            select(func.coalesce(func.max(SessionParticipant.guest_sequence), 0)).where(
                SessionParticipant.session_id == session_id,
                SessionParticipant.participant_type == ParticipantType.GUEST,
            )
        )
        or 0
    ) + 1
    name = data.name.strip() if data.name and data.name.strip() else f"Guest {next_seq:02d}"

    note = data.note
    if data.referred_by:
        note = f"Khách của {data.referred_by}" + (f" — {note}" if note else "")

    participant = SessionParticipant(
        session_id=session_id,
        member_id=None,
        participant_name=name,
        participant_type=ParticipantType.GUEST,
        skill_level=data.skill_level,
        skill_score=default_score_for(data.skill_level),
        attendance_source=AttendanceSource.GUEST,
        attendance_status=AttendanceStatus.CONFIRMED,
        note=note,
        guest_sequence=next_seq,
    )
    db.add(participant)
    audit_service.record(db, session_id=session_id, action="ADD_GUEST", payload={"name": name})
    db.commit()
    db.refresh(participant)
    return participant


def update_participant(
    db: Session, session_id: str, participant_id: str, data: UpdateParticipantRequest
) -> SessionParticipant:
    session = get_session(db, session_id)
    _ensure_editable(session.status)
    participant = _get_participant(db, session_id, participant_id)

    updates = data.model_dump(exclude_unset=True)
    skill_level_changed = "skill_level" in updates
    for field, value in updates.items():
        setattr(participant, field, value)
    if skill_level_changed and "skill_score" not in updates:
        # Session-scoped override only — Member master skill is untouched (BR-04).
        participant.skill_score = default_score_for(participant.skill_level)

    db.commit()
    db.refresh(participant)
    return participant


def remove_participant(db: Session, session_id: str, participant_id: str) -> None:
    session = get_session(db, session_id)
    _ensure_editable(session.status)
    participant = _get_participant(db, session_id, participant_id)
    db.delete(participant)
    audit_service.record(
        db, session_id=session_id, action="REMOVE_PARTICIPANT", payload={"participant_id": participant_id}
    )
    db.commit()
