import os

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "price-events")

# Redis Configuration for Celery
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/price_db")

# Backend API Configuration
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://backend:8000")
