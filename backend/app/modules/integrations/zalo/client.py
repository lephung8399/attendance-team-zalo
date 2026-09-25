"""Thin Zalo OA/GMF API client — placeholder pending the technical spike in
business-requirements.md #68 (PoC bắt buộc trước khi khoá kiến trúc integration).

Nothing here is wired into the app; core business logic never imports this
module directly, only through the AttendanceProvider / MessagePublisher
interfaces so a real implementation can be dropped in later.
"""

from dataclasses import dataclass


@dataclass
class ZaloConfig:
    oa_access_token: str | None = None
    group_id: str | None = None


class ZaloClient:
    """Placeholder for the real Zalo OA / GMF HTTP client (Phase 2).

    Token must live server-side only (spec NFR "Security", #63) — never sent
    to the frontend, never logged in plaintext.
    """

    def __init__(self, config: ZaloConfig):
        self._config = config

    def get_group_members(self) -> list[dict]:
        raise NotImplementedError("Zalo PoC pending — see docs/spec/business-requirements.md #68")

    def get_poll_votes(self, poll_id: str) -> list[dict]:
        raise NotImplementedError("Zalo PoC pending — see docs/spec/business-requirements.md #68")

    def send_group_message(self, group_id: str, text: str) -> dict:
        raise NotImplementedError("Zalo PoC pending — see docs/spec/business-requirements.md #68")
