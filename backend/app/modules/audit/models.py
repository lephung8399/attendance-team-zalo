from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.database import Base


class AuditLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Records key actions (generate/move/swap/finalize/publish) per BR-05
    and to seed future AI training data (technical-architecture.md)."""

    __tablename__ = "audit_logs"

    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("match_sessions.id", ondelete="CASCADE"), index=True
    )
    action: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    performed_by: Mapped[str] = mapped_column(String(120), default="admin")
