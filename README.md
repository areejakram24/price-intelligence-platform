# Distributed Event-Driven AI Price Intelligence Platform

A production-grade, containerized microservices architecture that ingests, streams, and analyzes product pricing data in real time. The platform features an automated background crawler pipeline, a high-throughput message broker network, and an unsupervised Machine Learning engine compiled to ONNX for low-latency anomaly detection and streaming analytics.

## Key Features

* **Decoupled Microservices:** 9 independent service containers orchestrated with deterministic dependency health checks.
* **Automated Task Scheduling:** Apache Airflow workflows dynamically triggering distributed Celery workers via a Redis broker.
* **High-Throughput Streaming:** Real-time data fabric utilizing a single-node Kafka cluster (KRaft mode) and structured Google Protocol Buffers (Protobuf) for optimized binary serialization.
* **Edge-Speed AI Inference:** Unsupervised Isolation Forest model cross-compiled to an optimized ONNX binary structure for microsecond-level price anomaly classification.
* **Production Observability:** Complete telemetry infrastructure featuring automated Prometheus target scraping and a custom Grafana analytics dashboard with a 5-second live refresh rate.

## Tech Stack Matrix

| Layer | Technologies |
| :--- | :--- |
| **Core Runtime** | Python 3.11, JavaScript, TypeScript |
| **Streaming & Messaging** | Apache Kafka (KRaft), Celery, Redis, Protocol Buffers |
| **AI & Machine Learning** | Scikit-learn, ONNX Runtime, NumPy, Pandas |
| **Backend Frameworks** | FastAPI, Uvicorn, SQLAlchemy |
| **Databases** | PostgreSQL 15, Redis |
| **DevOps & Infrastructure** | Docker, Docker Compose, Apache Airflow |
| **Observability Stack** | Prometheus, Grafana |
