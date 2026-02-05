# GitHub secrets & project env vars (what to add where)

This file lists every secret and environment variable this project uses, why it’s needed, and where to add it.

## Repository secrets (GitHub → Settings → Secrets and variables → Actions)
Add these as **Repository secrets** so Actions (migrations and publish workflows) can use them:

- `DATABASE_URL` (required)
  - postgresql+asyncpg://postgres:%2BRqP%3FEB.%246x33qa@db.elkxvlseokyjzbvevtas.supabase.co:5432/postgres
  - Note: remove the square brackets and use the encoded password exactly (no brackets). See `SUPABASE.md` for encoding instructions.
- `SECRET_KEY` (required)
  - A long random string used for signing JWTs. Example generator: `python -c "import secrets; print(secrets.token_hex(32))"`.
- `OPENAI_API_KEY` (optional)
  - If you want model calls to work on the backend (OpenAI paid or API key).

- `SENTRY_DSN` (optional)
  - For Sentry error reporting (optional). Sentry is not required; the app will run fine without it.
- `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` (optional)
  - For the `publish.yml` workflow that builds & pushes Docker images.

## Environment variables to set on Render/Vercel
- On Render (Backend service):
  - `DATABASE_URL` (the same secret from Supabase)
  - `SECRET_KEY` (private; same as GitHub secret if you prefer)
  - `APP_ENV` = `production`
  - `OPENAI_API_KEY`, `FRONTEND_URL`
- On Vercel (Frontend project):
  - `VITE_API_URL` = `https://<your-backend-url>/api` (exposed to client; do NOT publish sensitive backend secrets here)

## Local development
- Use `.env` (copy from `.env.example`) with local values. DO NOT commit `.env` to Git. Local `.env` is for developer convenience only.

## How to add a secret in GitHub
1. Go to your repo → Settings → Secrets and variables → Actions → New repository secret.  
2. Enter the secret name (e.g., `DATABASE_URL`) and its value, then Save.

## Notes & best practices
- Treat these values as secrets — never commit them.  
- For `DATABASE_URL` in Supabase, the connection string will be `postgres://...`; convert to `postgresql+asyncpg://...` when using with this repo’s async DB setup.  
- `APP_ENV` is not secret; set it to `production` on Render/Vercel to disable dev-only behaviors (e.g., returning reset tokens in responses).

---
If you'd like, I can add a small GitHub Actions job to validate that all required secrets are present and fail early with a helpful message; should I add that? (Yes/No)
