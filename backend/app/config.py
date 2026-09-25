from functools import lru_cache

from pydantic import Field
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

    # Zalo Bot Platform (https://bot.zaloplatforms.com) — Phase 2 integration.
    # Deliberately read WITHOUT the APP_ prefix (plain env var names) so they
    # can be set once in the environment's secret store independent of the
    # app's other config. Both must be set for real Zalo to activate; leaving
    # either unset keeps the app on NullMessagePublisher / manual attendance,
    # per the "Zalo is not core" principle (business-requirements.md #72).
    zalo_bot_token: str | None = Field(default=None, validation_alias="ZALO_BOT_TOKEN")
    zalo_group_chat_id: str | None = Field(default=None, validation_alias="ZALO_GROUP_CHAT_ID")
    zalo_bot_api_base_url: str = Field(
        default="https://bot-api.zapps.me", validation_alias="ZALO_BOT_API_BASE_URL"
    )
    zalo_checkin_keyword: str = Field(default="tham gia", validation_alias="ZALO_CHECKIN_KEYWORD")


@lru_cache
def get_settings() -> Settings:
    return Settings()
