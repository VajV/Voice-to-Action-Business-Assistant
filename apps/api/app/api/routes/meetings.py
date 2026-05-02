import json
from typing import Annotated
from uuid import uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Meeting, SourceType
from app.db.session import SessionLocal, get_db
from app.schemas.analysis import ActionItem, MeetingAnalysisPayload
from app.schemas.meeting import (
    ActionItemsUpdateRequest,
    IntegrationSendResponse,
    MeetingCreateResponse,
    MeetingProgress,
    MeetingResponse,
    MeetingResultResponse,
    NotionSendRequest,
    SlackSendRequest,
    SlackSendResponse,
    TrelloSendRequest,
    YouTubeImportRequest,
)
from app.services.notion import send_to_notion
from app.services.slack import send_to_slack
from app.services.storage import InvalidUploadError, save_upload
from app.services.trello import create_trello_cards
from app.services.youtube import YouTubeImportError, download_youtube_audio
from app.workers.tasks import process_meeting

router = APIRouter(prefix="/api/meetings", tags=["meetings"])
DbSession = Annotated[Session, Depends(get_db)]
AudioFile = Annotated[UploadFile, File()]
MeetingTitle = Annotated[str, Form()]
MeetingLanguage = Annotated[str, Form()]


def run_processing_job(meeting_id: str) -> None:
    db = SessionLocal()
    try:
        process_meeting(db, meeting_id)
    finally:
        db.close()


def serialize_meeting(meeting: Meeting) -> MeetingResponse:
    return MeetingResponse(
        id=meeting.id,
        title=meeting.title,
        source_type=meeting.source_type,
        language=meeting.language,
        status=meeting.status,
        progress=MeetingProgress(stage=meeting.progress_stage, percent=meeting.progress_percent),
        error_message=meeting.error_message,
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
    )


def get_meeting_or_404(db: Session, meeting_id: str) -> Meeting:
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


def build_analysis_payload(meeting: Meeting) -> MeetingAnalysisPayload:
    if meeting.analysis is None:
        raise HTTPException(status_code=404, detail="Meeting analysis is not ready")

    return MeetingAnalysisPayload(
        summary=meeting.analysis.summary,
        decisions=json.loads(meeting.analysis.decisions_json),
        action_items=[
            ActionItem.model_validate(item)
            for item in json.loads(meeting.analysis.action_items_json)
        ],
        risks=json.loads(meeting.analysis.risks_json),
        follow_up_questions=json.loads(meeting.analysis.follow_up_questions_json),
    )


def create_meeting_record(
    db: Session,
    title: str,
    source_type: SourceType,
    audio_file_path: str,
    language: str,
    source_url: str | None = None,
) -> Meeting:
    meeting = Meeting(
        id=f"meeting_{uuid4().hex}",
        title=title,
        source_type=source_type,
        source_url=source_url,
        audio_file_path=audio_file_path,
        language=language,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.post("", response_model=MeetingCreateResponse, status_code=201)
async def create_meeting(
    background_tasks: BackgroundTasks,
    file: AudioFile,
    db: DbSession,
    title: MeetingTitle = "Untitled meeting",
    language: MeetingLanguage = "auto",
) -> MeetingCreateResponse:
    try:
        audio_path = await save_upload(file)
    except InvalidUploadError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    meeting = create_meeting_record(
        db=db,
        title=title,
        source_type=SourceType.upload,
        audio_file_path=str(audio_path),
        language=language,
    )

    background_tasks.add_task(run_processing_job, meeting.id)
    return MeetingCreateResponse(id=meeting.id, status=meeting.status, title=meeting.title)


@router.post("/youtube", response_model=MeetingCreateResponse, status_code=201)
def create_youtube_meeting(
    payload: YouTubeImportRequest,
    background_tasks: BackgroundTasks,
    db: DbSession,
) -> MeetingCreateResponse:
    try:
        audio_path = download_youtube_audio(payload.url)
    except YouTubeImportError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    meeting = create_meeting_record(
        db=db,
        title=payload.title,
        source_type=SourceType.youtube,
        source_url=payload.url,
        audio_file_path=str(audio_path),
        language=payload.language,
    )

    background_tasks.add_task(run_processing_job, meeting.id)
    return MeetingCreateResponse(id=meeting.id, status=meeting.status, title=meeting.title)


@router.get("", response_model=list[MeetingResponse])
def list_meetings(
    db: DbSession,
    limit: int = Query(default=10, ge=1, le=50),
) -> list[MeetingResponse]:
    meetings = db.scalars(
        select(Meeting).order_by(Meeting.created_at.desc()).limit(limit)
    ).all()
    return [serialize_meeting(meeting) for meeting in meetings]


@router.get("/{meeting_id}", response_model=MeetingResponse)
def get_meeting(meeting_id: str, db: DbSession) -> MeetingResponse:
    return serialize_meeting(get_meeting_or_404(db, meeting_id))


@router.get("/{meeting_id}/result", response_model=MeetingResultResponse)
def get_meeting_result(meeting_id: str, db: DbSession) -> MeetingResultResponse:
    meeting = get_meeting_or_404(db, meeting_id)
    if meeting.transcript is None:
        raise HTTPException(status_code=404, detail="Meeting transcript is not ready")

    analysis = build_analysis_payload(meeting)
    return MeetingResultResponse(transcript=meeting.transcript.text, **analysis.model_dump())


@router.patch("/{meeting_id}/action-items", response_model=MeetingResultResponse)
def update_meeting_action_items(
    meeting_id: str,
    payload: ActionItemsUpdateRequest,
    db: DbSession,
) -> MeetingResultResponse:
    meeting = get_meeting_or_404(db, meeting_id)
    if meeting.transcript is None or meeting.analysis is None:
        raise HTTPException(status_code=404, detail="Meeting result is not ready")

    meeting.analysis.action_items_json = json.dumps(
        [item.model_dump() for item in payload.action_items], ensure_ascii=False
    )
    db.add(meeting.analysis)
    db.commit()
    db.refresh(meeting)

    analysis = build_analysis_payload(meeting)
    return MeetingResultResponse(transcript=meeting.transcript.text, **analysis.model_dump())


@router.post("/{meeting_id}/send/slack", response_model=SlackSendResponse)
async def send_meeting_to_slack(
    meeting_id: str,
    payload: SlackSendRequest,
    db: DbSession,
) -> SlackSendResponse:
    meeting = get_meeting_or_404(db, meeting_id)
    analysis = build_analysis_payload(meeting)

    try:
        await send_to_slack(payload.webhook_url, meeting.title, analysis)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="Slack delivery failed. Please verify your webhook URL.",
        ) from error

    return SlackSendResponse(ok=True, message="Meeting summary sent to Slack")


@router.post("/{meeting_id}/send/notion", response_model=IntegrationSendResponse)
async def send_meeting_to_notion(
    meeting_id: str,
    payload: NotionSendRequest,
    db: DbSession,
) -> IntegrationSendResponse:
    meeting = get_meeting_or_404(db, meeting_id)
    analysis = build_analysis_payload(meeting)

    try:
        await send_to_notion(
            token=payload.token,
            database_id=payload.database_id,
            title=meeting.title,
            analysis=analysis,
            api_base_url=settings.notion_api_base_url,
        )
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="Notion delivery failed. Please verify your integration settings.",
        ) from error

    return IntegrationSendResponse(ok=True, message="Meeting summary sent to Notion")


@router.post("/{meeting_id}/send/trello", response_model=IntegrationSendResponse)
async def send_meeting_to_trello(
    meeting_id: str,
    payload: TrelloSendRequest,
    db: DbSession,
) -> IntegrationSendResponse:
    meeting = get_meeting_or_404(db, meeting_id)
    analysis = build_analysis_payload(meeting)

    try:
        created = await create_trello_cards(
            api_key=payload.api_key,
            token=payload.token,
            list_id=payload.list_id,
            meeting_title=meeting.title,
            action_items=analysis.action_items,
            api_base_url=settings.trello_api_base_url,
        )
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="Trello delivery failed. Please verify your integration settings.",
        ) from error

    return IntegrationSendResponse(ok=True, message=f"Created {created} Trello cards")
