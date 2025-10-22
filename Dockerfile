# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.8.3 \
    APP_HOME=/app

WORKDIR $APP_HOME

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl && \
    rm -rf /var/lib/apt/lists/*

COPY backend backend
COPY specs specs
COPY .env.example .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -e ./backend[dev]

EXPOSE 8080
ENV PORT=8080

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
