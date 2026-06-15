# AECE (Ethical Assessment & Explanation Engine)

Full-stack scaffold:

- Frontend: Next.js
- Backend: FastAPI
- Database: PostgreSQL

Core features included:

- Scenario input
- Ethical scoring (LLM-powered when `OPENAI_API_KEY` is set, otherwise heuristic fallback)
- Dashboard UI
- History storage in PostgreSQL (per `session_id`)

## Requirements

- Docker Desktop
- (Optional) Node.js + npm (if you want to run Next.js locally)
- Python (if you want to run FastAPI outside Docker)

## Run with Docker Compose

1. Copy `.env.example` to `.env` (optional; only needed for enabling OpenAI):
   - Set `OPENAI_API_KEY=` if you want LLM scoring.
2. Start services:
   ```powershell
   docker compose up --build
   ```
3. Backend health:
   - `http://localhost:8000/health`

## Environment variables

- `OPENAI_API_KEY`: enable LLM scoring
- `LLM_MODEL`: model used for scoring
- `CORS_ORIGINS`: allowed frontend origins

## API endpoints

- `POST /api/assessments`
  - body: `{ "scenario": "...", "session_id": "..." }`
- `GET /api/assessments?session_id=...&limit=50&offset=0`
- `GET /health`

## Next.js frontend

The `frontend/` app is scaffolded in a follow-up step. Once it exists, set:

- `NEXT_PUBLIC_API_URL=http://localhost:8000`

