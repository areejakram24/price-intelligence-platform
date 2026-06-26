import os
import random
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from celery import Celery

from services.backend.database import get_db, engine, Base
from services.backend.models import Product, PriceHistory
from services.shared.config import REDIS_URL

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] (Backend) %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles structured app startup and shutdown event hooks cleanly."""
    logger.info("Syncing metadata definitions with underlying storage engine...")
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("Tearing down application gateway resources...")

app = FastAPI(title="Event-Driven Price Intelligence API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


celery_client = Celery("price_scraper", broker=REDIS_URL)

SCRAPE_TRIGGERS = Counter("price_intelligence_scrape_triggers_total", "Cumulative scraper invocation counts", ["product_id"])
DB_RECORDS_GAUGE = Gauge("price_intelligence_db_records_total", "Total tracked pricing nodes present in repository")
DB_ANOMALIES_GAUGE = Gauge("price_intelligence_db_anomalies_total", "Total verified pricing anomalies flagged in repository")

MOCK_PRODUCTS = {
    "iphone-15": {"name": "iPhone 15 Pro", "base_price": 999.00, "category": "Smartphones"},
    "macbook-pro": {"name": "MacBook Pro 16-inch M3", "base_price": 1999.00, "category": "Laptops"},
    "playstation-5": {"name": "PlayStation 5 Slim", "base_price": 499.00, "category": "Gaming Consoles"},
    "airpods-pro": {"name": "AirPods Pro (2nd Gen)", "base_price": 249.00, "category": "Audio"},
}

LATEST_PRICE_GAUGES = {
    product_id: Gauge(f"price_intelligence_latest_price_{product_id.replace('-', '_')}", f"Latest scraped tracking price for {product_id}")
    for product_id in MOCK_PRODUCTS.keys()
}

mock_prices = {k: v["base_price"] for k, v in MOCK_PRODUCTS.items()}

@app.get("/")
def read_root():
    return {"status": "healthy", "service": "price-intelligence-api-gateway"}


# --- Sandboxed Target Endpoint for Stochastic Price Simulation ---
@app.get("/mock/shop/{product_id}")
def mock_shop_product(product_id: str):
    if product_id not in MOCK_PRODUCTS:
        raise HTTPException(status_code=404, detail="Requested identity not found in target store catalog")
        
    base = MOCK_PRODUCTS[product_id]
    current = mock_prices[product_id]
    
    rand = random.random()
    if rand < 0.90:
        change = random.uniform(-0.025, 0.025)
        new_price = current * (1 + change)
        new_price = max(base["base_price"] * 0.7, min(base["base_price"] * 1.3, new_price))
    elif rand < 0.95:
        new_price = base["base_price"] * random.uniform(0.1, 0.3)  # Flash sale drop anomaly
        logger.warning(f"[Stochastic Simulation] Injecting low-price anomaly vector for {product_id}: {new_price:.2f}")
    else:
        new_price = base["base_price"] * random.uniform(2.5, 4.0)  # Supply shortage spike anomaly
        logger.warning(f"[Stochastic Simulation] Injecting high-price anomaly vector for {product_id}: {new_price:.2f}")
        
    mock_prices[product_id] = round(new_price, 2)
    
    return {
        "id": product_id,
        "name": base["name"],
        "price": mock_prices[product_id],
        "currency": "USD",
        "url": f"http://backend:8000/mock/shop/{product_id}",
        "source": "mock-store"
    }


# Core System Application Gateways 
@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    """Returns catalog assets enriched with their aggregated metrics via a single optimized query map."""
    products = db.query(Product).all()
    results = []
    
    for p in products:

        stats = db.query(
            func.avg(PriceHistory.price).label("avg"),
            func.min(PriceHistory.price).label("min"),
            func.max(PriceHistory.price).label("max"),
            func.count(PriceHistory.id).label("count")
        ).filter(PriceHistory.product_id == p.id).first()

        latest = db.query(PriceHistory).filter(PriceHistory.product_id == p.id).order_by(PriceHistory.timestamp.desc()).first()
        
        results.append({
            "id": p.id,
            "name": p.name,
            "url": p.url,
            "source": p.source,
            "category": p.category,
            "created_at": p.created_at,
            "latest_price": latest.price if latest else None,
            "currency": latest.currency if latest else "USD",
            "is_anomaly": latest.is_anomaly if latest else False,
            "anomaly_confidence": latest.anomaly_confidence if latest else 0.0,
            "last_updated": latest.timestamp if latest else None,
            "stats": {
                "avg": round(float(stats.avg), 2) if stats.avg else 0.0,
                "min": round(float(stats.min), 2) if stats.min else 0.0,
                "max": round(float(stats.max), 2) if stats.max else 0.0,
                "count": stats.count or 0
            }
        })
    return results

@app.get("/products/{product_id}/history")
def get_product_history(product_id: str, limit: int = 100, db: Session = Depends(get_db)):
    """Returns chronological slice vectors used directly by UI visualization charts."""
    history = db.query(PriceHistory).filter(PriceHistory.product_id == product_id).order_by(PriceHistory.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": h.id,
            "price": h.price,
            "currency": h.currency,
            "timestamp": h.timestamp,
            "is_anomaly": h.is_anomaly,
            "anomaly_confidence": h.anomaly_confidence
        } for h in reversed(history)
    ]

@app.post("/scrape")
def trigger_scrape(product_id: str, db: Session = Depends(get_db)):
    """Dispatches asynchronous scraping job commands directly into Celery workers."""
    if product_id not in MOCK_PRODUCTS:
        raise HTTPException(status_code=404, detail="Product ID out of bounds of scraper capabilities matrix")
        
    url = f"http://backend:8000/mock/shop/{product_id}"
    
    SCRAPE_TRIGGERS.labels(product_id=product_id).inc()
    
    try:
        task = celery_client.send_task("tasks.scrape_product", args=[url, product_id])
        logger.info(f"Successfully committed tracing task token to Celery -> Task ID: {task.id}")
        return {"status": "queued", "task_id": task.id, "product_id": product_id}
    except Exception as e:
        logger.error(f"Broker queue transaction failure: {e}")
        raise HTTPException(status_code=500, detail="Unable to safely register execution request downstream")


# Prometheus Target Hook
@app.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    """Dynamically serializes runtime state snapshots and converts them into Prometheus text payloads."""
    try:
        total_events = db.query(PriceHistory).count()
        total_anomalies = db.query(PriceHistory).filter(PriceHistory.is_anomaly == True).count()
        
        DB_RECORDS_GAUGE.set(total_events)
        DB_ANOMALIES_GAUGE.set(total_anomalies)
        
        for product_id, gauge in LATEST_PRICE_GAUGES.items():
            latest = db.query(PriceHistory).filter(PriceHistory.product_id == product_id).order_by(PriceHistory.timestamp.desc()).first()
            if latest:
                gauge.set(latest.price)
                
    except Exception as e:
        logger.error(f"Telemetry sync step fault: {e}")
        
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)