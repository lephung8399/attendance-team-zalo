from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    `database_url` defaults to a local SQLite file so the backend runs with
    zero external dependencies in dev/CI; docker-compose overrides it with the
    PostgreSQL DSN for anything resembling production, per the technical spec.
    """

    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_")

    database_url: str = "sqlite:///./attendance.db"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Skill scoring defaults (business-requirements.md #10-11)
    skill_score_gioi: float = 3.0
    skill_score_trung_binh: float = 2.0
    skill_score_yeu: float = 1.0
    skill_score_unknown: float = 2.0

    # Team configuration suggestion rules (business-requirements.md #21)
    preferred_team_size: int = 7
    min_team_size: int = 6
    max_team_size: int = 8
    preferred_team_counts: list[int] = [2, 3]

    # Balancing engine (business-requirements.md #28)
    balancing_iterations: int = 500
    balancing_tie_tolerance: float = 0.01

    default_team_colors: list[str] = ["WHITE", "RED", "BLUE", "YELLOW", "BLACK", "GREEN"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
