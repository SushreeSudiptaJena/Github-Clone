try:
    # Prefer explicit import from backend package
    from backend.app.main import app as app
except Exception:
    # Fallback: try importing from app package if running inside backend folder
    try:
        from app.main import app as app
    except Exception:
        raise
