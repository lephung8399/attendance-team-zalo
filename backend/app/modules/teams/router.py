from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.matches.schemas import MatchSessionOut
from app.modules.teams import service
from app.modules.teams.schemas import (
    GenerateTeamsRequest,
    MovePlayerRequest,
    SetColorsRequest,
    SwapRequest,
    TeamBoardOut,
    ToggleLockRequest,
)

router = APIRouter(prefix="/api/sessions/{session_id}", tags=["teams"])


@router.get("/teams", response_model=TeamBoardOut)
def get_board(session_id: str, db: Session = Depends(get_db)):
    return service.get_board(db, session_id)


@router.post("/generate-teams", response_model=TeamBoardOut)
def generate_teams(session_id: str, payload: GenerateTeamsRequest, db: Session = Depends(get_db)):
    return service.generate_teams(
        db, session_id, iterations=payload.iterations, regenerate_locked=payload.regenerate_locked
    )


@router.post("/teams/move-player", response_model=TeamBoardOut)
def move_player(session_id: str, payload: MovePlayerRequest, db: Session = Depends(get_db)):
    return service.move_player(db, session_id, payload.participant_id, payload.target_team_id)


@router.post("/teams/swap", response_model=TeamBoardOut)
def swap(session_id: str, payload: SwapRequest, db: Session = Depends(get_db)):
    return service.swap_players(db, session_id, payload.participant_id_a, payload.participant_id_b)


@router.post("/teams/lock", response_model=TeamBoardOut)
def toggle_lock(session_id: str, payload: ToggleLockRequest, db: Session = Depends(get_db)):
    return service.toggle_lock(db, session_id, payload.participant_id, payload.is_locked)


@router.patch("/teams/colors", response_model=TeamBoardOut)
def set_colors(session_id: str, payload: SetColorsRequest, db: Session = Depends(get_db)):
    return service.set_colors(db, session_id, payload.colors)


@router.post("/finalize", response_model=MatchSessionOut)
def finalize(session_id: str, db: Session = Depends(get_db)):
    return service.finalize(db, session_id)


@router.post("/reopen", response_model=MatchSessionOut)
def reopen(session_id: str, db: Session = Depends(get_db)):
    return service.reopen(db, session_id)
