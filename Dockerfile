# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOME=/app \
    PYTHONPATH=/app

WORKDIR $APP_HOME

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl && \
    rm -rf /var/lib/apt/lists/*

COPY backend backend
COPY specs specs
COPY .env.example .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir \
        'fastapi>=0.115,<1.0' \
        'uvicorn[standard]>=0.30,<1.0' \
        'pydantic>=2.7,<3.0' \
        'httpx>=0.27,<1.0' \
        'supabase>=2.22,<3.0' \
        'qdrant-client>=1.9,<2.0' \
        'apscheduler>=3.10,<4.0' \
        'openai>=1.40,<3.0' \
        'anthropic>=0.34,<1.0' \
        'python-dotenv>=1.0,<2.0'

EXPOSE 8080
ENV PORT=8080

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
