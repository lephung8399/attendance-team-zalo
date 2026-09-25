from app.modules.attendance.providers import AttendanceProvider, ProviderParticipant
from app.modules.integrations.zalo.client import ZaloClient


class ZaloAttendanceProvider(AttendanceProvider):
    """Source A/B (Zalo Poll or bot check-in) — business-requirements.md #8.

    Not wired into any router yet: whether this is even feasible (reading
    poll/vote results via the public Zalo API) is exactly the open question
    from the mandatory technical spike (#68). Until confirmed, sessions use
    `ManualAttendanceProvider` and the rest of the system is unaffected.
    """

    def __init__(self, client: ZaloClient, poll_id: str):
        self._client = client
        self._poll_id = poll_id

    def get_participants(self) -> list[ProviderParticipant]:
        raise NotImplementedError(
            "Zalo poll/vote read access not yet confirmed — run the technical spike "
            "in docs/spec/business-requirements.md #68 before implementing this."
        )
