from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.common.enums import PublishStatus


class PublishPreviewOut(BaseModel):
    message: str


class PublishResultOut(BaseModel):
    success: bool
    message: str
    error: str | None = None
    attempt: int
    session_status: str


class PublishLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: PublishStatus
    error: str | None
    attempt: int
    created_at: datetime
