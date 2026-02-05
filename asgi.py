"""ASGI entrypoint exposing the FastAPI `app` instance.

This file avoids import ambiguity with packages named `app` by using a
unique module name (`asgi`). Gunicorn/uvicorn should import `asgi:app`.
"""
try:
    from backend.app.main import app
except Exception:
    from app.main import app
