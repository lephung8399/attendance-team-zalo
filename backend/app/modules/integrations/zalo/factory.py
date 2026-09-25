"""Wiring: build real Zalo objects only when both `ZALO_BOT_TOKEN` and
`ZALO_GROUP_CHAT_ID` are configured; otherwise callers fall back to the
manual/null defaults. This is the one place that decides "is Zalo live",
keeping that decision out of the core services (business-requirements.md #72).
"""

from sqlalchemy.orm import Session

from app.config import get_settings
from app.modules.integrations.zalo.attendance_provider import ZaloCheckinAttendanceProvider
from app.modules.integrations.zalo.client import ZaloBotClient
from app.modules.integrations.zalo.publisher import ZaloMessagePublisher


def is_zalo_configured() -> bool:
    settings = get_settings()
    return bool(settings.zalo_bot_token and settings.zalo_group_chat_id)


def build_zalo_client() -> ZaloBotClient | None:
    settings = get_settings()
    if not settings.zalo_bot_token:
        return None
    return ZaloBotClient(token=settings.zalo_bot_token, base_url=settings.zalo_bot_api_base_url)


def build_zalo_publisher() -> ZaloMessagePublisher | None:
    settings = get_settings()
    client = build_zalo_client()
    if client is None or not settings.zalo_group_chat_id:
        return None
    return ZaloMessagePublisher(client, settings.zalo_group_chat_id)


def build_zalo_checkin_provider(db: Session) -> ZaloCheckinAttendanceProvider | None:
    settings = get_settings()
    client = build_zalo_client()
    if client is None or not settings.zalo_group_chat_id:
        return None
    return ZaloCheckinAttendanceProvider(
        db, client, settings.zalo_group_chat_id, settings.zalo_checkin_keyword
    )
