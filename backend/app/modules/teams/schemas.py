from pydantic import BaseModel, ConfigDict

from app.modules.attendance.schemas import ParticipantOut


class TeamMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    participant: ParticipantOut


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    name: str
    color: str
    strength_score: float
    order: int
    members: list[ParticipantOut] = []


class TeamBoardOut(BaseModel):
    teams: list[TeamOut]
    reserve: list[ParticipantOut]
    balance: "BalanceSummary"


class BalanceSummary(BaseModel):
    strengths: list[float]
    difference: float
    label: str


class GenerateTeamsRequest(BaseModel):
    iterations: int | None = None
    # False (default) = "Generate Unlocked Players": locked players keep their
    # current team. True = "Generate All": reshuffle everyone, ignoring locks.
    regenerate_locked: bool = False


class MovePlayerRequest(BaseModel):
    participant_id: str
    target_team_id: str | None = None  # None => move to Reserve


class SwapRequest(BaseModel):
    participant_id_a: str
    participant_id_b: str


class SetColorsRequest(BaseModel):
    colors: dict[str, str]  # team_id -> color


class ToggleLockRequest(BaseModel):
    participant_id: str
    is_locked: bool
