# Voice-to-Action Business Assistant

MVP web app that turns meeting audio into:

- a transcript;
- a short summary;
- key decisions;
- structured action items;
- a Slack-ready update.

The repository is a monorepo:

```text
apps/
  api/  FastAPI backend
  web/  Next.js frontend
```

## MVP flow

```text
Audio upload → transcription → AI analysis → action items → Slack webhook
```

## Current MVP scope

Implemented:

- upload `.mp3`, `.wav`, `.m4a`, `.webm`;
- meeting lifecycle: queued, processing, transcribed, completed, failed;
- demo transcription and analysis fallback without credentials;
- optional OpenAI transcription/analysis when `OPENAI_API_KEY` is configured and `DEMO_MODE=false`;
- result page with transcript, summary, decisions, risks, follow-up questions, and action items;
- Slack Incoming Webhook delivery;
- FastAPI tests for the core backend flow.

Deferred to later versions:

- YouTube import via `yt-dlp`;
- microphone recording;
- OAuth for Slack/Notion/Trello;
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
DEMO_MODE=true
DATABASE_URL=sqlite:///./voice_to_action.db
LOCAL_STORAGE_DIR=./storage
FRONTEND_URL=http://localhost:3000
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

`DEMO_MODE=true` lets the app run without OpenAI credentials using deterministic demo output.

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
