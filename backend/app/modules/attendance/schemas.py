from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.common.enums import AttendanceStatus, ParticipantType, SkillLevel


class ParticipantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    member_id: str | None
    participant_name: str
    participant_type: ParticipantType
    skill_level: SkillLevel
    skill_score: float
    attendance_status: AttendanceStatus
    is_substitute: bool
    is_locked: bool
    note: str | None


class SyncAttendanceRequest(BaseModel):
    """Manual/import attendance sync (Source C, business-requirements.md #8).

    `member_ids` come from existing Member master data; a Zalo-backed sync
    would populate the same SessionParticipant rows via a different
    AttendanceProvider implementation without changing this contract.
    """

    member_ids: list[str] = []


class AddParticipantRequest(BaseModel):
    member_id: str
    skill_level_override: SkillLevel | None = None


class AddGuestRequest(BaseModel):
    name: str | None = None
    skill_level: SkillLevel = SkillLevel.UNKNOWN
    referred_by: str | None = None
    note: str | None = None


class UpdateParticipantRequest(BaseModel):
    participant_name: str | None = None
    skill_level: SkillLevel | None = None
    attendance_status: AttendanceStatus | None = None
    is_substitute: bool | None = None
    is_locked: bool | None = None
    note: str | None = None
