FROM python:3.11-slim

# Copy entire repository into the image so builds work whether Docker's build
# context is the repo root or the `backend` subfolder. Then install whichever
# requirements file is available (prefer backend/requirements.txt).
WORKDIR /app/backend
COPY . /app
RUN if [ -f /app/backend/requirements.txt ]; then \
			pip install --no-cache-dir -r /app/backend/requirements.txt; \
		elif [ -f /app/requirements.txt ]; then \
			pip install --no-cache-dir -r /app/requirements.txt; \
		else \
			echo "No requirements file found"; exit 1; \
		fi

# Ensure Python can import the `app` package located at /app/backend and top-level
# `app.py` at /app
ENV PYTHONPATH=/app:/app/backend

# Use Gunicorn with a single Uvicorn worker and bind to the runtime $PORT
CMD ["sh", "-c", "gunicorn -w 1 -k uvicorn.workers.UvicornWorker asgi:app --bind 0.0.0.0:${PORT:-8000}"]

# rebuild: $(date -u)