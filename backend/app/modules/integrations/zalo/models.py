from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.common.mixins import UUIDPrimaryKeyMixin
from app.database import Base


class ZaloPollState(UUIDPrimaryKeyMixin, Base):
    """Singleton row tracking the last Zalo `getUpdates` offset consumed.

    Needed for idempotent polling (spec NFR #63): each check-in message must
    be attributed to attendance exactly once even if "Sync Zalo" is clicked
    repeatedly or two Admins click it around the same time.
    """

    __tablename__ = "zalo_poll_state"

    last_update_id: Mapped[int] = mapped_column(Integer, default=0)
