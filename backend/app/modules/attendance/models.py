from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import AttendanceSource, AttendanceStatus, ParticipantType, SkillLevel
from app.common.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.database import Base


class SessionParticipant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A member or guest participating in one MatchSession (business-requirements.md #14-18).

    Skill is snapshotted at session time (#15) so editing a Member's master
    skill later never rewrites history.
    """

    __tablename__ = "session_participants"

    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("match_sessions.id", ondelete="CASCADE"), index=True
    )
    member_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("members.id", ondelete="SET NULL"), nullable=True
    )
    participant_name: Mapped[str] = mapped_column(String(120))
    participant_type: Mapped[ParticipantType] = mapped_column(
        SAEnum(ParticipantType, native_enum=False, length=20)
    )
    skill_level: Mapped[SkillLevel] = mapped_column(SAEnum(SkillLevel, native_enum=False, length=20))
    skill_score: Mapped[float] = mapped_column(default=2.0)
    attendance_source: Mapped[AttendanceSource] = mapped_column(
        SAEnum(AttendanceSource, native_enum=False, length=20)
    )
    attendance_status: Mapped[AttendanceStatus] = mapped_column(
        SAEnum(AttendanceStatus, native_enum=False, length=20), default=AttendanceStatus.CONFIRMED
    )
    is_substitute: Mapped[bool] = mapped_column(Boolean, default=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    guest_sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)
