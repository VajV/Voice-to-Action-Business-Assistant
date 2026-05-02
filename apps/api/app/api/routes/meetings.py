import json
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.models import Meeting, SourceType
from app.db.session import SessionLocal, get_db
from app.schemas.analysis import ActionItem, MeetingAnalysisPayload
from app.schemas.meeting import (
    MeetingCreateResponse,
    MeetingProgress,
    MeetingResponse,
    MeetingResultResponse,
    SlackSendRequest,
    SlackSendResponse,
)
from app.services.slack import send_to_slack
from app.services.storage import InvalidUploadError, save_upload
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

    meeting = Meeting(
        id=f"meeting_{uuid4().hex}",
        title=title,
        source_type=SourceType.upload,
        audio_file_path=str(audio_path),
        language=language,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    background_tasks.add_task(run_processing_job, meeting.id)
    return MeetingCreateResponse(id=meeting.id, status=meeting.status, title=meeting.title)


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
