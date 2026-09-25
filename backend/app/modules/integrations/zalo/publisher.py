from app.modules.integrations.zalo.client import ZaloBotClient, ZaloBotError
from app.modules.publishing.publishers import MessagePublisher, PublishOutcome


class ZaloMessagePublisher(MessagePublisher):
    """Real Zalo Bot Platform publisher (business-requirements.md #46-49).

    Sends the finalized team message straight into the group chat via
    `sendMessage` — no webhook or public domain needed for this direction.
    """

    def __init__(self, client: ZaloBotClient, chat_id: str):
        self._client = client
        self._chat_id = chat_id

    def send_message(self, text: str) -> PublishOutcome:
        try:
            self._client.send_message(self._chat_id, text)
            return PublishOutcome(success=True)
        except ZaloBotError as exc:
            return PublishOutcome(success=False, error=str(exc))
