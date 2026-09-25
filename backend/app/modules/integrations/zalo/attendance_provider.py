from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import MemberStatus, SkillLevel
from app.common.skill import default_score_for
from app.modules.attendance.providers import AttendanceProvider, ProviderParticipant
from app.modules.integrations.zalo.client import ZaloBotClient
from app.modules.integrations.zalo.models import ZaloPollState
from app.modules.members.models import Member


class ZaloCheckinAttendanceProvider(AttendanceProvider):
    """Source B (business-requirements.md #8): members type a check-in keyword
    (e.g. "tham gia") in the Zalo group; we pick it up via `getUpdates`
    instead of reading a poll, since the Bot Platform exposes no
    poll/vote-reading API at all (confirmed by inspecting the official SDK).

    A sender with no Member yet (no matching `zalo_user_id`) is
    auto-registered as a new Member — this is the FR-02 "Zalo Mapping" the
    spec asks for, seeded organically as people check in rather than
    requiring a manual import first.
    """

    def __init__(self, db: Session, client: ZaloBotClient, chat_id: str, keyword: str):
        self._db = db
        self._client = client
        self._chat_id = chat_id
        self._keyword = keyword.strip().lower()

    def get_participants(self) -> list[ProviderParticipant]:
        state = self._db.query(ZaloPollState).first()
        if state is None:
            state = ZaloPollState(last_update_id=0)
            self._db.add(state)
            self._db.flush()

        # offset = last_update_id + 1 acknowledges everything up to and
        # including last_update_id, per the Bot API's documented contract —
        # this is what makes repeated "Sync Zalo" clicks idempotent (NFR #63).
        offset = state.last_update_id + 1 if state.last_update_id else None
        updates = self._client.get_updates(offset=offset, limit=100, timeout=0)

        participants: list[ProviderParticipant] = []
        max_update_id = state.last_update_id
        for update in updates:
            max_update_id = max(max_update_id, update.update_id)
            if update.chat_id != self._chat_id:
                continue
            if self._keyword not in update.text.strip().lower():
                continue

            member = self._db.scalar(select(Member).where(Member.zalo_user_id == update.sender_zalo_id))
            if member is None:
                member = Member(
                    zalo_user_id=update.sender_zalo_id,
                    display_name=update.sender_display_name,
                    skill_level=SkillLevel.UNKNOWN,
                    skill_score=default_score_for(SkillLevel.UNKNOWN),
                    status=MemberStatus.ACTIVE,
                )
                self._db.add(member)
                self._db.flush()

            participants.append(
                ProviderParticipant(
                    member_id=member.id,
                    display_name=member.display_name,
                    skill_level=member.skill_level,
                )
            )

        state.last_update_id = max_update_id
        self._db.flush()
        return participants
