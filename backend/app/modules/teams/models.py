from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import AssignedBy
from app.common.mixins import UUIDPrimaryKeyMixin, utcnow
from app.database import Base


class Team(UUIDPrimaryKeyMixin, Base):
    """One team within a MatchSession (business-requirements.md #39)."""

    __tablename__ = "teams"

    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("match_sessions.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(60))
    color: Mapped[str] = mapped_column(String(20))
    strength_score: Mapped[float] = mapped_column(Float, default=0.0)
    order: Mapped[int] = mapped_column(Integer, default=0)


class TeamMember(UUIDPrimaryKeyMixin, Base):
    """Assignment of one SessionParticipant to one Team (business-requirements.md #40).

    `participant_id` is unique: a participant belongs to at most one Team
    (BR-01) — a participant not present here and not in the Reserve bucket is
    considered unassigned.
    """

    __tablename__ = "team_members"

    team_id: Mapped[str] = mapped_column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    participant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("session_participants.id", ondelete="CASCADE"), unique=True
    )
    assigned_by: Mapped[AssignedBy] = mapped_column(
        SAEnum(AssignedBy, native_enum=False, length=20), default=AssignedBy.SYSTEM
    )
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
