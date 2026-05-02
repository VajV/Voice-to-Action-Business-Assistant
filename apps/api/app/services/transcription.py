from pathlib import Path

from openai import OpenAI

from app.core.config import settings


class TranscriptionService:
    def transcribe(self, audio_path: Path, language: str = "auto") -> tuple[str, str, str]:
        if settings.demo_mode or not settings.openai_api_key:
            return (
                "Демо-транскрипт встречи: команда договорилась запустить MVP, "
                "подготовить лендинг, настроить Slack-интеграцию и проверить качество "
                "распознавания на русских и английских созвонах.",
                language,
                "demo",
            )

        client = OpenAI(api_key=settings.openai_api_key)
        with audio_path.open("rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=settings.openai_transcription_model,
                file=audio_file,
                language=None if language == "auto" else language,
            )

        return transcript.text, language, settings.openai_transcription_model
