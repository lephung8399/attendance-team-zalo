from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.exceptions import ValidationFailedError
from app.database import get_db
from app.modules.attendance import service
from app.modules.attendance.providers import ManualAttendanceProvider, ProviderParticipant
from app.modules.attendance.schemas import (
    AddGuestRequest,
    AddParticipantRequest,
    ParticipantOut,
    SyncAttendanceRequest,
    UpdateParticipantRequest,
)
from app.modules.integrations.zalo.factory import build_zalo_checkin_provider
from app.modules.members.models import Member

router = APIRouter(prefix="/api/sessions/{session_id}", tags=["attendance"])


@router.post("/sync-attendance", response_model=list[ParticipantOut])
def sync_attendance(session_id: str, payload: SyncAttendanceRequest, db: Session = Depends(get_db)):
    members = db.query(Member).filter(Member.id.in_(payload.member_ids)).all()
    provider_participants = [
        ProviderParticipant(member_id=m.id, display_name=m.display_name, skill_level=m.skill_level)
        for m in members
    ]
    provider = ManualAttendanceProvider(provider_participants)
    return service.sync_attendance(db, session_id, provider)


@router.post("/sync-attendance/zalo", response_model=list[ParticipantOut])
def sync_attendance_from_zalo(session_id: str, db: Session = Depends(get_db)):
    """Source B (business-requirements.md #8): pull anyone who has typed the
    check-in keyword in the Zalo group since the last sync. 400s with a clear
    message if ZALO_BOT_TOKEN/ZALO_GROUP_CHAT_ID aren't configured yet."""
    provider = build_zalo_checkin_provider(db)
    if provider is None:
        raise ValidationFailedError(
            "Chưa cấu hình Zalo (ZALO_BOT_TOKEN / ZALO_GROUP_CHAT_ID). Dùng đồng bộ thủ công bên dưới."
        )
    return service.sync_attendance(db, session_id, provider)


@router.get("/participants", response_model=list[ParticipantOut])
def list_participants(session_id: str, db: Session = Depends(get_db)):
    return service.list_participants(db, session_id)


@router.post("/participants", response_model=ParticipantOut, status_code=201)
def add_participant(session_id: str, payload: AddParticipantRequest, db: Session = Depends(get_db)):
    return service.add_member_participant(db, session_id, payload.member_id, payload.skill_level_override)


@router.patch("/participants/{participant_id}", response_model=ParticipantOut)
def update_participant(
    session_id: str, participant_id: str, payload: UpdateParticipantRequest, db: Session = Depends(get_db)
):
    return service.update_participant(db, session_id, participant_id, payload)


@router.delete("/participants/{participant_id}", status_code=204)
def remove_participant(session_id: str, participant_id: str, db: Session = Depends(get_db)):
    service.remove_participant(db, session_id, participant_id)


@router.post("/guests", response_model=ParticipantOut, status_code=201)
def add_guest(session_id: str, payload: AddGuestRequest, db: Session = Depends(get_db)):
    return service.add_guest(db, session_id, payload)
