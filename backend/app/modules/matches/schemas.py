from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict

from app.common.enums import SessionStatus


class MatchSessionCreate(BaseModel):
    title: str
    play_date: date
    start_time: time | None = None
    location: str | None = None
    zalo_group_id: str | None = None


class MatchSessionUpdate(BaseModel):
    title: str | None = None
    play_date: date | None = None
    start_time: time | None = None
    location: str | None = None
    status: SessionStatus | None = None


class TeamConfigurationUpdate(BaseModel):
    team_count: int
    player_per_team: int
    substitute_count: int


class TeamConfigurationSuggestion(BaseModel):
    team_count: int
    player_per_team: int
    substitute_count: int
    total: int
    recommended: bool = False


class MatchSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    play_date: date
    start_time: time | None
    location: str | None
    zalo_group_id: str | None
    poll_id: str | None
    status: SessionStatus
    team_count: int | None
    player_per_team: int | None
    substitute_count: int | None
    created_by: str
    created_at: datetime
    updated_at: datetime


class MatchSessionSummary(MatchSessionOut):
    participant_count: int = 0
