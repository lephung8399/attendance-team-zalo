from app.config import get_settings


def default_colors_for(team_count: int) -> list[str]:
    """Default color assignment (business-requirements.md #37-38): WHITE/RED/BLUE
    first, cycling through the extended palette if there are more teams than
    default colors provide."""
    settings = get_settings()
    palette = settings.default_team_colors
    return [palette[i % len(palette)] for i in range(team_count)]
