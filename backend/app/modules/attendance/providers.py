"""Attendance Provider abstraction (business-requirements.md #6-8).

Business logic must never depend on Zalo directly. Anything that can produce
a list of `ProviderParticipant` can back a session's attendance sync — manual
selection today, a real `ZaloAttendanceProvider` later
(see app/modules/integrations/zalo/attendance_provider.py) without touching
this module or the sync service below.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.common.enums import SkillLevel


@dataclass(frozen=True)
class ProviderParticipant:
    member_id: str
    display_name: str
    skill_level: SkillLevel | None = None


class AttendanceProvider(ABC):
    @abstractmethod
    def get_participants(self) -> list[ProviderParticipant]:
        """Return the current list of confirmed participants from the source."""


class ManualAttendanceProvider(AttendanceProvider):
    """Source C (fallback, always available): Admin explicitly picks members."""

    def __init__(self, participants: list[ProviderParticipant]):
        self._participants = participants

    def get_participants(self) -> list[ProviderParticipant]:
        return self._participants
