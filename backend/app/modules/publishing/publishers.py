"""MessagePublisher abstraction (business-requirements.md #6-7, #46-49).

Publishing must never depend on Zalo directly, mirroring the AttendanceProvider
side of the adapter. `NullMessagePublisher` is the MVP default — it always
reports failure with a clear reason so the mandatory `Copy Message` fallback
is always what Admins actually use until `ZaloMessagePublisher`
(app/modules/integrations/zalo/publisher.py) is wired up in Phase 2.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class PublishOutcome:
    success: bool
    error: str | None = None


class MessagePublisher(ABC):
    @abstractmethod
    def send_message(self, text: str) -> PublishOutcome:
        """Send `text` to the target channel (e.g. a Zalo group)."""


class NullMessagePublisher(MessagePublisher):
    """Default MVP publisher: no Zalo channel is configured yet."""

    def send_message(self, text: str) -> PublishOutcome:
        return PublishOutcome(
            success=False,
            error="Zalo chưa được kết nối cho buổi đá này. Vui lòng dùng Copy Message.",
        )
