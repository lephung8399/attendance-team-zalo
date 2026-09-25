"""Thin HTTP client for the Zalo Bot Platform (https://bot.zaloplatforms.com).

Contract confirmed by reading the official `python-zalo-bot` SDK source (it is
modeled directly on Telegram's Bot API) rather than guessing from docs we
could not reach from this environment:

    POST {base_url}/bot{token}/{method}
    body: JSON
    response: {"ok": bool, "result": ..., "description": str, "error_code": int}

Methods used here: `getMe`, `sendMessage`, `getUpdates`. There is no
poll/vote-reading endpoint in this API surface at all — confirming
business-requirements.md #8's "Source A" (reading a Zalo poll) is not
possible on this platform. Attendance instead comes from "Source B": members
type a check-in keyword in the group and we pick it up via `getUpdates`.
"""

from dataclasses import dataclass
from typing import Any

import httpx


class ZaloBotError(Exception):
    """Raised when the Zalo Bot API rejects a request or is unreachable."""


@dataclass(frozen=True)
class ZaloUpdate:
    update_id: int
    chat_id: str
    sender_zalo_id: str
    sender_display_name: str
    text: str


class ZaloBotClient:
    def __init__(self, token: str, base_url: str = "https://bot-api.zapps.me", timeout: float = 10.0):
        if not token:
            raise ValueError("Zalo bot token is required")
        self._base_url = f"{base_url}/bot{token}"
        self._timeout = timeout

    def _post(self, method: str, payload: dict[str, Any] | None = None) -> Any:
        try:
            response = httpx.post(f"{self._base_url}/{method}", json=payload or {}, timeout=self._timeout)
        except httpx.HTTPError as exc:
            raise ZaloBotError(f"Zalo Bot API '{method}' unreachable: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise ZaloBotError(f"Zalo Bot API '{method}' returned invalid JSON") from exc

        if not response.is_success or (isinstance(data, dict) and data.get("ok") is False):
            description = data.get("description") if isinstance(data, dict) else response.text
            raise ZaloBotError(f"Zalo Bot API '{method}' failed: {description}")

        return data.get("result") if isinstance(data, dict) and "result" in data else data

    def get_me(self) -> dict:
        return self._post("getMe")

    def send_message(self, chat_id: str, text: str) -> dict:
        return self._post("sendMessage", {"chat_id": chat_id, "text": text})

    def get_updates(self, offset: int | None = None, limit: int = 100, timeout: int = 0) -> list[ZaloUpdate]:
        """Fetch pending updates since `offset`.

        The reference SDK's wrapper only ever unpacks a single Update from the
        response, but its own docstring says to "recalculate offset after each
        server response" like Telegram's batched model — so we normalize
        defensively to a list here rather than assume either shape holds in
        all cases, and let the caller track `offset` from the max `update_id`
        seen.
        """
        payload: dict[str, Any] = {"limit": limit, "timeout": timeout}
        if offset is not None:
            payload["offset"] = offset
        result = self._post("getUpdates", payload)

        raw_updates: list[dict]
        if not result:
            raw_updates = []
        elif isinstance(result, list):
            raw_updates = result
        else:
            raw_updates = [result]

        updates: list[ZaloUpdate] = []
        for item in raw_updates:
            message = item.get("message") or {}
            chat = message.get("chat") or {}
            sender = message.get("from") or {}
            if "update_id" not in item or "text" not in message:
                continue
            updates.append(
                ZaloUpdate(
                    update_id=item["update_id"],
                    chat_id=str(chat.get("id", "")),
                    sender_zalo_id=str(sender.get("id", "")),
                    sender_display_name=sender.get("display_name") or "Zalo User",
                    text=message.get("text") or "",
                )
            )
        return updates
