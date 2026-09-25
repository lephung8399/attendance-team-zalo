from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import PublishStatus
from app.common.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.database import Base


class MessageTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Zalo message template (business-requirements.md #47). Content is never
    hard-coded — placeholders are substituted at publish time."""

    __tablename__ = "message_templates"

    name: Mapped[str] = mapped_column(String(120))
    content: Mapped[str] = mapped_column(Text)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)


class PublishLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Every publish attempt (business-requirements.md #48-49) — a failure must
    never lose the generated result, so this row always persists before the
    publisher is called."""

    __tablename__ = "publish_logs"

    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("match_sessions.id", ondelete="CASCADE"), index=True
    )
    message_content: Mapped[str] = mapped_column(Text)
    status: Mapped[PublishStatus] = mapped_column(SAEnum(PublishStatus, native_enum=False, length=20))
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt: Mapped[int] = mapped_column(Integer, default=1)
