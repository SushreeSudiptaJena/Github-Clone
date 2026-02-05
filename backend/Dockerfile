FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# Copy application
COPY ./app ./app
# copy alembic config so the container can run migrations
COPY ./alembic.ini ./alembic.ini
COPY ./alembic ./alembic
ENV PYTHONPATH=/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
