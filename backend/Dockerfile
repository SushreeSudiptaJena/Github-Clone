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

# Ensure Python can import the `app` package located at /app/backend/app
ENV PYTHONPATH=/app/backend

# Use shell form so we can expand $PORT at runtime (default 8000)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
