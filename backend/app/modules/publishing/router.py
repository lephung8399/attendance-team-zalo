from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.integrations.zalo.factory import build_zalo_publisher
from app.modules.publishing import service
from app.modules.publishing.schemas import PublishLogOut, PublishPreviewOut, PublishResultOut

router = APIRouter(prefix="/api/sessions/{session_id}", tags=["publishing"])


@router.get("/publish-preview", response_model=PublishPreviewOut)
def publish_preview(session_id: str, db: Session = Depends(get_db)):
    return PublishPreviewOut(message=service.preview_message(db, session_id))


@router.post("/publish", response_model=PublishResultOut)
def publish(session_id: str, db: Session = Depends(get_db)):
    # Uses the real Zalo publisher when ZALO_BOT_TOKEN + ZALO_GROUP_CHAT_ID are
    # configured; otherwise `service.publish` falls back to NullMessagePublisher
    # (Copy Message stays the guaranteed fallback either way).
    return service.publish(db, session_id, publisher=build_zalo_publisher())


@router.get("/publish-logs", response_model=list[PublishLogOut])
def publish_logs(session_id: str, db: Session = Depends(get_db)):
    return service.list_publish_logs(db, session_id)
