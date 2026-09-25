from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.publishing import service
from app.modules.publishing.schemas import PublishLogOut, PublishPreviewOut, PublishResultOut

router = APIRouter(prefix="/api/sessions/{session_id}", tags=["publishing"])


@router.get("/publish-preview", response_model=PublishPreviewOut)
def publish_preview(session_id: str, db: Session = Depends(get_db)):
    return PublishPreviewOut(message=service.preview_message(db, session_id))


@router.post("/publish", response_model=PublishResultOut)
def publish(session_id: str, db: Session = Depends(get_db)):
    return service.publish(db, session_id)


@router.get("/publish-logs", response_model=list[PublishLogOut])
def publish_logs(session_id: str, db: Session = Depends(get_db)):
    return service.list_publish_logs(db, session_id)
