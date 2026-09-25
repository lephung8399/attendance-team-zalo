from app.modules.integrations.zalo.client import ZaloClient
from app.modules.publishing.publishers import MessagePublisher, PublishOutcome


class ZaloMessagePublisher(MessagePublisher):
    """Real Zalo OA → group publisher (Phase 2). Requires the OA messaging
    permission confirmed by the technical spike (business-requirements.md #68)."""

    def __init__(self, client: ZaloClient, group_id: str):
        self._client = client
        self._group_id = group_id

    def send_message(self, text: str) -> PublishOutcome:
        try:
            self._client.send_group_message(self._group_id, text)
            return PublishOutcome(success=True)
        except NotImplementedError as exc:
            return PublishOutcome(success=False, error=str(exc))
