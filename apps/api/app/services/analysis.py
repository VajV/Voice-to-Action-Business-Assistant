import json

from openai import OpenAI
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.analysis import ActionItem, MeetingAnalysisPayload

SYSTEM_PROMPT = """You extract business meeting outcomes.
Return only valid JSON matching this schema:
{
  "summary": "string",
  "decisions": ["string"],
  "action_items": [
    {
      "title": "string",
      "owner": "string|null",
      "due_date": "YYYY-MM-DD|null",
      "priority": "low|medium|high",
      "context": "string",
      "confidence": 0.0
    }
  ],
  "risks": ["string"],
  "follow_up_questions": ["string"]
}
Do not invent owners or dates. Preserve the transcript language."""


class AnalysisService:
    def analyze(self, transcript: str) -> tuple[MeetingAnalysisPayload, str, str]:
        api_key = settings.openrouter_api_key or settings.openai_api_key
        base_url = settings.openai_base_url
        model = settings.openai_analysis_model

        if settings.openrouter_api_key:
            base_url = base_url or "https://openrouter.ai/api/v1"
            model = settings.openrouter_analysis_model

        if settings.demo_mode or not api_key:
            return (
                MeetingAnalysisPayload(
                    summary=(
                        "Команда согласовала запуск MVP Voice-to-Action Assistant "
                        "и первые интеграции."
                    ),
                    decisions=[
                        "Начать с загрузки аудио, транскрипции, извлечения задач и Slack webhook.",
                        "Notion, Trello, YouTube и запись микрофона перенести на следующие версии.",
                    ],
                    action_items=[
                        ActionItem(
                            title="Подготовить MVP backend и frontend",
                            owner=None,
                            due_date=None,
                            priority="high",
                            context=(
                                "Нужно реализовать основной путь от загрузки аудио "
                                "до результата."
                            ),
                            confidence=0.86,
                        ),
                        ActionItem(
                            title="Проверить Slack webhook отправку",
                            owner=None,
                            due_date=None,
                            priority="medium",
                            context="Slack выбран как первая интеграция для MVP.",
                            confidence=0.8,
                        ),
                    ],
                    risks=[
                        "Качество задач зависит от качества аудио и полноты транскрипции.",
                        "Для production нужны очереди и лимиты по длительности аудио.",
                    ],
                    follow_up_questions=[
                        "Нужна ли авторизация в первой публичной версии?",
                        "Какие форматы задач должны попадать в Notion/Trello в v1?",
                    ],
                ),
                "demo",
                "v1",
            )

        if base_url:
            client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": transcript},
            ],
        )
        content = response.choices[0].message.content or "{}"

        try:
            payload = MeetingAnalysisPayload.model_validate(json.loads(content))
        except (json.JSONDecodeError, ValidationError) as error:
            raise ValueError("AI analysis returned invalid structured output") from error

        return payload, model, "v1"
