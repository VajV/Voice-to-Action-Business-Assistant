# Voice-to-Action Business Assistant

MVP web app that turns meeting audio into:

- a transcript;
- a short summary;
- key decisions;
- structured action items;
- Slack, Notion, and Trello-ready updates.

The repository is a monorepo:

```text
apps/
  api/  FastAPI backend
  web/  Next.js frontend
```

## MVP flow

```text
Audio/YouTube input → transcription → AI analysis → editable action items → integrations
```

## Current MVP scope

Implemented:

- upload `.mp3`, `.wav`, `.m4a`, `.webm`;
- YouTube audio import via `yt-dlp`;
- meeting lifecycle: queued, processing, transcribed, completed, failed;
- demo transcription and analysis fallback without credentials;
- optional OpenAI transcription/analysis when `OPENAI_API_KEY` is configured and `DEMO_MODE=false`;
- OpenRouter-compatible AI analysis via `OPENROUTER_API_KEY`;
- recent meetings history;
- editable action items before sending them to integrations;
- result page with transcript, summary, decisions, risks, follow-up questions, and action items;
- Slack Incoming Webhook delivery;
- Notion database page creation;
- Trello card creation for action items;
- FastAPI tests for the core backend flow.

Deferred to later versions:

- microphone recording;
- OAuth for Slack/Notion/Trello instead of manual token/webhook entry;
- Celery/Redis production worker;
- PostgreSQL migrations via Alembic;
- user accounts and billing.

## Local setup

Copy environment defaults:

```bash
cp .env.example .env
```

### Backend

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

The API will run at `http://localhost:8000`.

### Frontend

```bash
cd apps/web
npm install
npm run dev
```

The frontend will run at `http://localhost:3000`.

### Docker Compose

```bash
docker compose up
```

## Environment variables

```env
OPENAI_API_KEY=
OPENAI_TRANSCRIPTION_MODEL=whisper-1
OPENAI_ANALYSIS_MODEL=gpt-4o-mini
OPENAI_BASE_URL=
OPENROUTER_API_KEY=
OPENROUTER_ANALYSIS_MODEL=nvidia/nemotron-3-super-120b-a12b:free
NOTION_API_BASE_URL=https://api.notion.com/v1
TRELLO_API_BASE_URL=https://api.trello.com/1
DEMO_MODE=true
DATABASE_URL=sqlite:///./voice_to_action.db
LOCAL_STORAGE_DIR=./storage
FRONTEND_URL=http://localhost:3000
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

`DEMO_MODE=true` lets the app run without OpenAI credentials using deterministic demo output.

For OpenRouter analysis, set:

```env
DEMO_MODE=false
OPENROUTER_API_KEY=your-openrouter-key
OPENROUTER_ANALYSIS_MODEL=nvidia/nemotron-3-super-120b-a12b:free
```

OpenRouter is used for transcript analysis. Audio transcription still requires a speech-to-text provider such as OpenAI Whisper, or the app can use demo transcription while validating the UI flow.

## API

### Health

```http
GET /health
```

### Create meeting

```http
POST /api/meetings
Content-Type: multipart/form-data
```

Fields:

- `file`;
- `title`;
- `language`.

### Import YouTube meeting

```http
POST /api/meetings/youtube
Content-Type: application/json
```

Body:

```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "title": "Customer interview",
  "language": "auto"
}
```

Requires `yt-dlp` and FFmpeg in the runtime image.

### List recent meetings

```http
GET /api/meetings?limit=10
```

### Get meeting status

```http
GET /api/meetings/{meeting_id}
```

### Get meeting result

```http
GET /api/meetings/{meeting_id}/result
```

### Send to Slack

```http
POST /api/meetings/{meeting_id}/send/slack
```

Body:

```json
{
  "webhook_url": "https://hooks.slack.com/services/..."
}
```

### Send to Notion

```http
POST /api/meetings/{meeting_id}/send/notion
```

Body:

```json
{
  "token": "secret_...",
  "database_id": "..."
}
```

### Send to Trello

```http
POST /api/meetings/{meeting_id}/send/trello
```

Body:

```json
{
  "api_key": "...",
  "token": "...",
  "list_id": "..."
}
```

### Update action items

```http
PATCH /api/meetings/{meeting_id}/action-items
```

Body:

```json
{
  "action_items": [
    {
      "title": "Prepare launch plan",
      "owner": "Alex",
      "due_date": "2026-05-10",
      "priority": "high",
      "context": "Needed before customer rollout",
      "confidence": 0.91
    }
  ]
}
```

## Tests and checks

Backend:

```bash
cd apps/api
pytest
ruff check .
```

Frontend:

```bash
cd apps/web
npm run typecheck
npm run lint
```

## Production notes

For real production usage, replace FastAPI `BackgroundTasks` with Celery/RQ + Redis, use PostgreSQL, store audio in object storage, encrypt integration credentials, add authentication, and add per-plan upload duration limits.
