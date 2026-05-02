import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models import Meeting, MeetingAnalysis, MeetingStatus, Transcript
from app.services.analysis import AnalysisService
from app.services.transcription import TranscriptionService


def update_progress(
    db: Session,
    meeting: Meeting,
    status: MeetingStatus,
    stage: str,
    percent: int,
) -> None:
    meeting.status = status
    meeting.progress_stage = stage
    meeting.progress_percent = percent
    db.add(meeting)
    db.commit()
    db.refresh(meeting)


def process_meeting(db: Session, meeting_id: str) -> None:
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        return

    try:
        update_progress(db, meeting, MeetingStatus.processing, "transcribing", 25)
        transcript_text, language, provider = TranscriptionService().transcribe(
            Path(meeting.audio_file_path), meeting.language
        )

        transcript = Transcript(
            meeting_id=meeting.id,
            text=transcript_text,
            language=language,
            provider=provider,
        )
        db.add(transcript)
        update_progress(db, meeting, MeetingStatus.transcribed, "analyzing", 60)

        payload, model, prompt_version = AnalysisService().analyze(transcript_text)
        analysis = MeetingAnalysis(
            meeting_id=meeting.id,
            summary=payload.summary,
            decisions_json=json.dumps(payload.decisions, ensure_ascii=False),
            action_items_json=json.dumps(
                [item.model_dump() for item in payload.action_items], ensure_ascii=False
            ),
            risks_json=json.dumps(payload.risks, ensure_ascii=False),
            follow_up_questions_json=json.dumps(payload.follow_up_questions, ensure_ascii=False),
            model=model,
            prompt_version=prompt_version,
        )
        db.add(analysis)
        update_progress(db, meeting, MeetingStatus.completed, "completed", 100)
    except Exception as error:
        db.rollback()
        meeting.status = MeetingStatus.failed
        meeting.error_message = str(error)
        meeting.progress_stage = "failed"
        db.add(meeting)
        db.commit()
