from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.matches import service
from app.modules.matches.schemas import (
    MatchSessionCreate,
    MatchSessionOut,
    MatchSessionSummary,
    MatchSessionUpdate,
    TeamConfigurationSuggestion,
    TeamConfigurationUpdate,
)
from app.modules.matches.suggestion import suggest_configurations

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=list[MatchSessionSummary])
def list_sessions(db: Session = Depends(get_db)):
    return service.list_sessions(db)


@router.post("", response_model=MatchSessionOut, status_code=201)
def create_session(payload: MatchSessionCreate, db: Session = Depends(get_db)):
    return service.create_session(db, payload)


@router.get("/{session_id}", response_model=MatchSessionOut)
def get_session(session_id: str, db: Session = Depends(get_db)):
    return service.get_session(db, session_id)


@router.patch("/{session_id}", response_model=MatchSessionOut)
def update_session(session_id: str, payload: MatchSessionUpdate, db: Session = Depends(get_db)):
    return service.update_session(db, session_id, payload)


@router.get("/{session_id}/team-suggestions", response_model=list[TeamConfigurationSuggestion])
def team_suggestions(session_id: str, db: Session = Depends(get_db)):
    count = service.count_active_participants(db, session_id)
    return suggest_configurations(count)


@router.patch("/{session_id}/configuration", response_model=MatchSessionOut)
def update_configuration(session_id: str, payload: TeamConfigurationUpdate, db: Session = Depends(get_db)):
    return service.update_configuration(db, session_id, payload)
