# Deploying Gemini-Clone for Free (Frontend on Vercel, Backend on Render)

This guide shows a simple free deployment split: frontend to Vercel, backend to Render. No paid integrations are required — the app will work without OpenAI/HuggingFace API keys (it falls back to a local echo). You can add API keys later if you want real LLM replies.

## Backend (Render - Free web service)

1. Push your repo to GitHub.
2. Go to https://render.com and create a free account.
3. Create a new "Web Service" and connect your GitHub repo.
   - Choose the `backend` folder as the root (Render allows selecting a subdirectory).
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Instance type: free (hobby)
4. Environment variables (optional):
   - `OPENAI_API_KEY` (leave empty for local echo)
   - `HUGGINGFACE_API_TOKEN` (optional)
   - `DATABASE_URL` (optional — by default the app uses SQLite in `./dev.db`)
5. Deploy. Render will build and expose a public URL like `https://your-service.onrender.com`.

Notes:
- The Dockerfile in `backend` has been updated to use the runtime `$PORT` when you deploy with Docker. If you use Render's build system (no Docker), use the Start command above.
- The app defaults to SQLite (`sqlite+aiosqlite:///./dev.db`) so you don't need a managed database.

## Frontend (Vercel - Free hosting)

1. From your GitHub repo, go to https://vercel.com and create a free account.
2. Import your project and set the project root to the `frontend` folder.
3. Build command: `npm run build` (Vercel will detect Vite automatically)
4. Output directory: `dist`
5. Add an environment variable (Project > Settings > Environment Variables):
   - `VITE_API_URL` = `https://your-backend-url` (set this to your Render service URL)
6. Deploy. Vercel will give you a public URL for the frontend.

## Local development

Backend (from repo root):

```bash
cd backend
python -m venv .venv
# Activate the venv (Windows)
.venv\Scripts\activate
pip install -r requirements.txt
# Run the app on port 8000
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Frontend (from repo root):

```bash
cd frontend
npm install
npm run dev
# Or build
npm run build
npm run preview
```

Set `VITE_API_URL` to `http://localhost:8000` for local testing if you want the frontend to call the local backend.

## Notes about LLM providers and costs

- The app will run without `OPENAI_API_KEY` or `HUGGINGFACE_API_TOKEN` but will return a local echo response instead of real model outputs.
- If you later want real LLM responses without cost, consider using hosted free community models on Hugging Face (may still require a token) or self-hosted models — both are more advanced and may need more resources.

## Next steps (optional)

- Add a small persistent managed DB if you want multi-instance durability (Render offers managed Postgres paid plans).
- If you want a single combined deploy (everything in one service), you can containerize both and deploy a single Docker app to a provider that supports multi-service containers — but that usually requires paid plans or more configuration.

If you want, I can:
- Commit these changes and a quick `README` update.
- Add a `Procfile` or Render manifest.
- Convert backend to a lightweight single-file deploy (e.g., using Deta) if you prefer tiny free hosts.
