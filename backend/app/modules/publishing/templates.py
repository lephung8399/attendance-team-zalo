"""Message template rendering (business-requirements.md #46-47).

Placeholders (`{{session_title}}`, `{{teams}}`, `{{reserves}}`, `{{location}}`,
`{{start_time}}`, `{{footer}}`) are substituted at publish/preview time —
content is never hard-coded so Admins can edit the template later.
"""

from app.modules.matches.models import MatchSession
from app.modules.teams.schemas import TeamBoardOut, TeamOut

DEFAULT_TEMPLATE = (
    "{{session_title}}\n\n"
    "{{teams}}\n\n"
    "{{reserves}}\n\n"
    "📍 {{location}}\n"
    "🕣 {{start_time}}\n\n"
    "{{footer}}"
)

DEFAULT_FOOTER = "Anh em đến trước giờ đá 10 phút."

COLOR_EMOJI = {
    "WHITE": "⚪",
    "RED": "🔴",
    "BLUE": "🔵",
    "YELLOW": "🟡",
    "BLACK": "⚫",
    "GREEN": "🟢",
}

COLOR_LABEL_VI = {
    "WHITE": "TRẮNG",
    "RED": "ĐỎ",
    "BLUE": "XANH DƯƠNG",
    "YELLOW": "VÀNG",
    "BLACK": "ĐEN",
    "GREEN": "XANH LÁ",
}


def _format_team(team: TeamOut) -> str:
    emoji = COLOR_EMOJI.get(team.color, "⚽")
    label = COLOR_LABEL_VI.get(team.color, team.color)
    lines = [f"{emoji} TEAM {label}"]
    lines += [f"{i}. {p.participant_name}" for i, p in enumerate(team.members, start=1)]
    return "\n".join(lines)


def _format_reserve(reserve: list) -> str:
    if not reserve:
        return ""
    lines = ["🔄 DỰ BỊ"] + [f"{i}. {p.participant_name}" for i, p in enumerate(reserve, start=1)]
    return "\n".join(lines)


def render_message(session: MatchSession, board: TeamBoardOut, template_content: str | None = None) -> str:
    content = template_content or DEFAULT_TEMPLATE
    replacements = {
        "{{session_title}}": f"⚽ CHIA ĐỘI - {session.title}",
        "{{teams}}": "\n\n".join(_format_team(t) for t in board.teams),
        "{{reserves}}": _format_reserve(board.reserve),
        "{{location}}": session.location or "(chưa cập nhật)",
        "{{start_time}}": session.start_time.strftime("%H:%M") if session.start_time else "(chưa cập nhật)",
        "{{footer}}": DEFAULT_FOOTER,
    }
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    # Collapse the extra blank line left behind when there's no reserve this week.
    return content.replace("\n\n\n", "\n\n")
