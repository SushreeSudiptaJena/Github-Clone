# Deploying to Render (quick guide)

This guide helps you deploy the backend (FastAPI) and frontend (Vite) using Render (free tier) and Vercel (optional). It assumes your code is pushed to GitHub.

## 1) Create accounts
- Render: https://render.com (recommended for backend & DB)
- Vercel: https://vercel.com (optional, for frontend instead of Render static service)

## 2) Connect your repo to Render
- Go to Render dashboard → New → Import from GitHub
- Select your repo `gemini-clone`
- Add two services (or use the `render.yaml` manifest added to repo):
  - `gemini-backend` (Web Service, Docker)
    - Dockerfile path: `backend/Dockerfile`
    - Environment: set `APP_ENV=production`
    - Add env vars: `SECRET_KEY`, `OPENAI_API_KEY` (optional), `FRONTEND_URL`
  - `gemini-frontend` (Static Site) OR deploy frontend to Vercel
    - Root: `frontend`
    - Build Command: `npm ci && npm run build`
    - Publish Directory: `dist`

## 3) Provision a managed Postgres on Render
- In Render, create a new Database (Starter plan)
- Copy the Database URL and set it as `DATABASE_URL` env var on the `gemini-backend` service

## 4) Run database migrations
- Option A: Use the job `run-migrations` defined in `render.yaml` (execute it from Render dashboard once DB is ready)
- Option B: From the `gemini-backend` service, select "Shell" and run:
  ```bash
  alembic upgrade head
  ```

> Note: A GitHub Action (`.github/workflows/migrate.yml`) has been added to this repo. It runs `alembic upgrade head` on `push` to `main` and can also be triggered manually via `workflow_dispatch`. To use it, add a repository secret named `DATABASE_URL` with your Supabase/Render DB connection string. This allows migrations to run automatically without manual intervention.

## 5) Configure environment variables
- On Render, set these env vars in the service settings (or use Render secrets):
  - `DATABASE_URL` (from managed DB)
  - `SECRET_KEY` (generate a long random value)
  - `APP_ENV=production`
  - `OPENAI_API_KEY` (if using OpenAI)
  - Email-based password reset is not supported. Password changes are available only via the authenticated `change-password` endpoint.
  - `FRONTEND_URL` (e.g., `https://your-frontend-on-vercel-or-render`)

## 6) Deploy frontend (Vercel recommended)
- Connect the same GitHub repo to Vercel
- Set Environment Variable in Vercel: `VITE_API_URL` → the Render backend URL (e.g., `https://gemini-backend.onrender.com/api`)
- Deploy the project; Vercel will build and publish the React app

## 7) Verify and test
- Visit the frontend URL and try sign up/login and chat
- Check backend health: `GET https://<backend-url>/api/health`
- Check logs in Render for any errors

## 8) Backups (manual)
- Use `scripts/backup_db.sh` to take a dump from anywhere that has `DATABASE_URL` set
- Consider scheduling backups to S3 via a GitHub Action or an external cron if desired

---
If you'd like, I can:
- Add a GitHub Action to run migrations automatically after successful backend deploy
- Add a small `render-secret-setup.md` that lists exact env values to set
- Customize `render.yaml` with your GitHub repo URL and branch

Which would you like me to add next? (I can add `render.yaml` with your repo filled in, a GitHub Action for migrations, or a short `render-secret-setup.md`.)
