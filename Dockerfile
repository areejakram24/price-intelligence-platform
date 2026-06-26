FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for compiling psycopg2 and general building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements for all services
COPY services/backend/requirements.txt ./backend_reqs.txt
COPY services/scraper/requirements.txt ./scraper_reqs.txt
COPY services/consumer/requirements.txt ./consumer_reqs.txt

RUN pip install --no-cache-dir -r backend_reqs.txt
RUN pip install --no-cache-dir -r scraper_reqs.txt
RUN pip install --no-cache-dir -r consumer_reqs.txt

# Copy codebase
COPY services/ ./services/

# Set Python Path to resolve services.* modules
ENV PYTHONPATH=/app

# Default command (can be overridden by docker-compose)
CMD ["uvicorn", "services.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
