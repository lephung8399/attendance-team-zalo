from datetime import date, time

from sqlalchemy import Date, Enum as SAEnum, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import SessionStatus
from app.common.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.database import Base


class MatchSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single "buổi đá" (business-requirements.md #12)."""

    __tablename__ = "match_sessions"

    title: Mapped[str] = mapped_column(String(200))
    play_date: Mapped[date] = mapped_column(Date)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    zalo_group_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    poll_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[SessionStatus] = mapped_column(
        SAEnum(SessionStatus, native_enum=False, length=20), default=SessionStatus.DRAFT
    )

    # Team configuration (business-requirements.md #19-23) — nullable until Admin
    # confirms a configuration; validated together in matches/service.py.
    team_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    player_per_team: Mapped[int | None] = mapped_column(Integer, nullable=True)
    substitute_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_by: Mapped[str] = mapped_column(String(120), default="admin")
