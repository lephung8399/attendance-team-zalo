"""Tests for the real Zalo Bot Platform adapter.

The HTTP contract asserted here (`POST {base}/bot{token}/{method}`, envelope
`{"ok", "result"}`) was confirmed by reading the official `python-zalo-bot`
SDK source, not guessed — see client.py's module docstring. We stub the
transport instead of hitting the network so these tests are fast/offline and
never need a real bot token.
"""

import httpx
import pytest

from app.common.enums import SkillLevel
from app.modules.integrations.zalo.attendance_provider import ZaloCheckinAttendanceProvider
from app.modules.integrations.zalo.client import ZaloBotClient, ZaloBotError
from app.modules.integrations.zalo.publisher import ZaloMessagePublisher
from app.modules.members.models import Member


def _client_with_transport(monkeypatch, handler) -> ZaloBotClient:
    def fake_post(url, json=None, timeout=None):
        request = httpx.Request("POST", url, json=json)
        transport = httpx.MockTransport(handler)
        with httpx.Client(transport=transport) as c:
            return c.send(request)

    monkeypatch.setattr(httpx, "post", fake_post)
    return ZaloBotClient(token="fake-token")


def test_send_message_success(monkeypatch):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = request.content
        return httpx.Response(200, json={"ok": True, "result": {"message_id": "1"}})

    client = _client_with_transport(monkeypatch, handler)
    result = client.send_message("zgr-abc", "hello")

    assert result == {"message_id": "1"}
    assert captured["url"].endswith("/botfake-token/sendMessage")
    assert b'"chat_id":"zgr-abc"' in captured["body"] or b'"chat_id": "zgr-abc"' in captured["body"]


def test_send_message_api_error_raises(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": False, "description": "invalid chat_id"})

    client = _client_with_transport(monkeypatch, handler)
    with pytest.raises(ZaloBotError, match="invalid chat_id"):
        client.send_message("bad-chat", "hi")


def test_publisher_reports_failure_as_outcome(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": False, "description": "chat not found"})

    client = _client_with_transport(monkeypatch, handler)
    publisher = ZaloMessagePublisher(client, "zgr-abc")

    outcome = publisher.send_message("some message")

    assert outcome.success is False
    assert "chat not found" in outcome.error


def test_get_updates_normalizes_single_and_list_results(monkeypatch):
    raw_update = {
        "update_id": 5,
        "message": {
            "message_id": "m1",
            "chat": {"id": "zgr-abc", "chat_type": "GROUP"},
            "from": {"id": "u1", "display_name": "Minh"},
            "text": "tham gia",
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": raw_update})

    client = _client_with_transport(monkeypatch, handler)
    updates = client.get_updates()

    assert len(updates) == 1
    assert updates[0].update_id == 5
    assert updates[0].chat_id == "zgr-abc"
    assert updates[0].sender_zalo_id == "u1"
    assert updates[0].text == "tham gia"


def test_checkin_provider_registers_new_member_and_advances_offset(db_session, monkeypatch):
    updates_batches = iter(
        [
            [
                {
                    "update_id": 10,
                    "message": {
                        "chat": {"id": "zgr-group"},
                        "from": {"id": "zalo-u1", "display_name": "Nam"},
                        "text": "Tham Gia nhé",
                    },
                },
                {
                    "update_id": 11,
                    "message": {
                        "chat": {"id": "zgr-other-group"},
                        "from": {"id": "zalo-u2", "display_name": "Someone Else"},
                        "text": "tham gia",
                    },
                },
            ]
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        batch = next(updates_batches, [])
        return httpx.Response(200, json={"ok": True, "result": batch})

    client = _client_with_transport(monkeypatch, handler)
    provider = ZaloCheckinAttendanceProvider(db_session, client, "zgr-group", "tham gia")

    participants = provider.get_participants()

    assert len(participants) == 1  # the other group's message is filtered out
    member = db_session.query(Member).filter_by(zalo_user_id="zalo-u1").one()
    assert member.display_name == "Nam"
    assert member.skill_level == SkillLevel.UNKNOWN
    assert participants[0].member_id == member.id

    from app.modules.integrations.zalo.models import ZaloPollState

    state = db_session.query(ZaloPollState).one()
    assert state.last_update_id == 11
