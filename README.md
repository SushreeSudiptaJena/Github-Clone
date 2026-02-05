# Gemini Clone (FastAPI + React + Tailwind)

Minimal hackathon-ready scaffold for an AI chat app:
- Backend: FastAPI, OpenAI adapter, WebSocket streaming, Postgres (via docker-compose)
- Frontend: React + Vite + Tailwind, WebSocket streaming UI

Quick start (local with docker):

1. Copy `backend/.env.example` → `backend/.env` and set `OPENAI_API_KEY`, `SECRET_KEY` (required), and `FRONTEND_URL`.
2. From project root run the helper script to start everything:
   - Unix: `scripts/start-dev.sh`
   - Windows: `scripts\start-dev.bat`
   This runs `docker-compose up --build`. The backend runs migrations on start and serves on http://localhost:8000; the frontend is at http://localhost:3000.

Run backend without Docker (dev):

1. python -m venv venv
2. source venv/bin/activate (or venv\Scripts\activate on Windows)
3. pip install -r backend/requirements.txt
4. copy `backend/.env.example` -> `backend/.env` and set values (OPENAI_API_KEY optional, SECRET_KEY required)
5. Run migrations: `./backend/scripts/run_migrations.sh` (or `backend\scripts\run_migrations.bat` on Windows)
6. cd backend
7. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Database migrations (Alembic):

1. Ensure `DATABASE_URL` is set in your environment or `backend/.env`.
2. From project root: `alembic -c backend/alembic.ini upgrade head` or use the helper script `backend/scripts/run_migrations.sh`
3. To autogenerate a migration after model changes:
   - `alembic -c backend/alembic.ini revision --autogenerate -m "Describe change"`
   - `alembic -c backend/alembic.ini upgrade head`

Note: Alembic will read `DATABASE_URL` environment variable; for async URLs (postgresql+asyncpg://) the migration tool will convert to a sync URL by removing the `+asyncpg` suffix when running migrations.
Notes:
- Backend listens on http://localhost:8000
- WebSocket chat endpoint: ws://localhost:8000/ws/chat
- Sessions: create and select chat sessions in the frontend sidebar; chats are persisted to Postgres per session.

Authentication and password reset:
- Registration requires username >= 3 chars and password >= 8 chars. Optionally provide an email for password resets.
- Request password reset: POST `/api/request-password-reset` with `{ "username": "..." }` or `{ "email": "..." }`. If a SendGrid API key and user email are configured, a reset link (and HTML email) is sent to the user containing a link to the frontend with the reset token as a query parameter (e.g. `https://app.example/?reset_token=...`). In development without SendGrid the reset token and a preview link are returned in the API response for convenience.
- Reset password: POST `/api/reset-password` with `{ "token": "...", "new_password": "..." }`.
- Change password (authenticated): POST `/api/change-password` with `{ "token": "old_password", "new_password": "..." }`.

Swap model provider by editing `backend/app/openai_adapter.py` — it provides a simple adapter pattern.

This scaffold is a starting point; for production please add authentication, secure secrets, robust error handling, and migrations.
