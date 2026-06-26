FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY services/backend/requirements.txt ./backend_reqs.txt
COPY services/scraper/requirements.txt ./scraper_reqs.txt
COPY services/consumer/requirements.txt ./consumer_reqs.txt
COPY services/ml_training/requirements.txt ./ml_training_reqs.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend_reqs.txt && \
    pip install --no-cache-dir -r scraper_reqs.txt && \
    pip install --no-cache-dir -r consumer_reqs.txt && \
    pip install --no-cache-dir -r ml_training_reqs.txt

COPY services/ ./services/

ENV PYTHONPATH=/app
default
CMD ["uvicorn", "services.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]