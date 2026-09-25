"""Team configuration auto-suggestion (business-requirements.md #19-23).

Rules are configurable (app/config.py) rather than hard-coded, per spec #21.
"""

from app.config import get_settings
from app.modules.matches.schemas import TeamConfigurationSuggestion


def suggest_configurations(participant_count: int) -> list[TeamConfigurationSuggestion]:
    settings = get_settings()
    n = participant_count
    if n <= 0:
        return []

    candidates: list[TeamConfigurationSuggestion] = []
    for team_count in settings.preferred_team_counts:
        if team_count <= 0:
            continue
        best_for_team_count: list[TeamConfigurationSuggestion] = []
        for player_per_team in range(settings.max_team_size, settings.min_team_size - 1, -1):
            capacity = team_count * player_per_team
            if capacity > n:
                continue
            reserve = n - capacity
            best_for_team_count.append(
                TeamConfigurationSuggestion(
                    team_count=team_count,
                    player_per_team=player_per_team,
                    substitute_count=reserve,
                    total=n,
                )
            )
        # Keep at most the two best options per team_count: fewest reserves,
        # tie-broken by closeness to preferred_team_size.
        best_for_team_count.sort(
            key=lambda c: (c.substitute_count, abs(c.player_per_team - settings.preferred_team_size))
        )
        candidates.extend(best_for_team_count[:2])

    if not candidates:
        return []

    candidates.sort(
        key=lambda c: (c.substitute_count, abs(c.player_per_team - settings.preferred_team_size))
    )
    candidates[0].recommended = True
    return candidates[:4]


def validate_configuration(
    *, team_count: int, player_per_team: int, substitute_count: int, participant_count: int
) -> list[str]:
    """Returns a list of human-readable issues; empty list means valid (spec #23)."""
    issues: list[str] = []
    if team_count < 1:
        issues.append("Số đội phải lớn hơn 0.")
    if player_per_team < 1:
        issues.append("Số người mỗi đội phải lớn hơn 0.")
    if substitute_count < 0:
        issues.append("Số dự bị không được âm.")
    total_assigned = team_count * player_per_team + substitute_count
    if total_assigned != participant_count:
        diff = participant_count - total_assigned
        if diff > 0:
            issues.append(
                f"{team_count} × {player_per_team} + {substitute_count} = {total_assigned}. "
                f"Còn {diff} người chưa được phân bổ."
            )
        else:
            issues.append(
                f"{team_count} × {player_per_team} + {substitute_count} = {total_assigned}. "
                f"Dư {-diff} chỗ so với số người tham gia."
            )
    return issues
