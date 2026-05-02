from datetime import datetime

from pydantic import BaseModel

from app.db.models import MeetingStatus, SourceType
from app.schemas.analysis import MeetingAnalysisPayload


class MeetingProgress(BaseModel):
    stage: str
    percent: int


class MeetingCreateResponse(BaseModel):
    id: str
    status: MeetingStatus
    title: str


class MeetingResponse(BaseModel):
    id: str
    title: str
    source_type: SourceType
    language: str
    status: MeetingStatus
    progress: MeetingProgress
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class MeetingResultResponse(MeetingAnalysisPayload):
    transcript: str


class SlackSendRequest(BaseModel):
    webhook_url: str


class SlackSendResponse(BaseModel):
    ok: bool
    message: str
