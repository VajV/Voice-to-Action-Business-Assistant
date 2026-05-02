from datetime import datetime

from pydantic import BaseModel, field_validator

from app.db.models import MeetingStatus, SourceType
from app.schemas.analysis import ActionItem, MeetingAnalysisPayload


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


class ActionItemsUpdateRequest(BaseModel):
    action_items: list[ActionItem]


class YouTubeImportRequest(BaseModel):
    url: str
    title: str = "YouTube meeting"
    language: str = "auto"

    @field_validator("url")
    @classmethod
    def validate_youtube_url(cls, value: str) -> str:
        if not value.startswith(("https://www.youtube.com/", "https://youtube.com/", "https://youtu.be/")):
            raise ValueError("Only YouTube URLs are supported")
        return value


class SlackSendRequest(BaseModel):
    webhook_url: str

    @field_validator("webhook_url")
    @classmethod
    def validate_slack_webhook_url(cls, value: str) -> str:
        allowed_prefixes = (
            "https://hooks.slack.com/services/",
            "https://hooks.slack.com/workflows/",
        )
        if not value.startswith(allowed_prefixes):
            raise ValueError("Slack webhook URL must use a Slack hooks URL")
        return value


class SlackSendResponse(BaseModel):
    ok: bool
    message: str


class NotionSendRequest(BaseModel):
    token: str
    database_id: str


class TrelloSendRequest(BaseModel):
    api_key: str
    token: str
    list_id: str


class IntegrationSendResponse(BaseModel):
    ok: bool
    message: str
