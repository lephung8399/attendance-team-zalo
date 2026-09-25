from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import MemberStatus, SkillLevel
from app.common.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.database import Base


class Member(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Master data for a fixed group member (business-requirements.md #9)."""

    __tablename__ = "members"

    zalo_user_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    display_name: Mapped[str] = mapped_column(String(120))
    nickname: Mapped[str | None] = mapped_column(String(60), nullable=True)
    skill_level: Mapped[SkillLevel] = mapped_column(
        SAEnum(SkillLevel, native_enum=False, length=20), default=SkillLevel.UNKNOWN
    )
    skill_score: Mapped[float] = mapped_column(Float, default=2.0)
    preferred_position: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[MemberStatus] = mapped_column(
        SAEnum(MemberStatus, native_enum=False, length=20), default=MemberStatus.ACTIVE
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
