from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.common.enums import MemberStatus, SkillLevel


class MemberBase(BaseModel):
    display_name: str
    nickname: str | None = None
    zalo_user_id: str | None = None
    skill_level: SkillLevel = SkillLevel.UNKNOWN
    skill_score: float | None = None
    preferred_position: str | None = None
    note: str | None = None


class MemberCreate(MemberBase):
    pass


class MemberUpdate(BaseModel):
    display_name: str | None = None
    nickname: str | None = None
    zalo_user_id: str | None = None
    skill_level: SkillLevel | None = None
    skill_score: float | None = None
    preferred_position: str | None = None
    status: MemberStatus | None = None
    note: str | None = None


class MemberOut(MemberBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: MemberStatus
    skill_score: float
    created_at: datetime
    updated_at: datetime
