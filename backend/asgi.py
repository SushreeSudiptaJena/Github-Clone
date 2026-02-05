"""ASGI entrypoint copied into `backend/` so it's available inside Docker build
context when Render builds from the `backend` folder.

Gunicorn/uvicorn should import `asgi:app`.
"""
try:
    from backend.app.main import app
except Exception:
    from app.main import app
