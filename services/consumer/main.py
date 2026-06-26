import asyncio
import os
import logging
from datetime import datetime, timezone
import numpy as np
from aiokafka import AIOKafkaConsumer


from services.backend.database import SessionLocal, engine, Base
from services.backend.models import Product, PriceHistory
from services.backend.onnx_inference import detector
from services.shared.price_event_pb2 import PriceEvent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] (Consumer) %(message)s")
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "price-events")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "price-intelligence-consumers")

logger.info("Syncing relational database structural layout abstractions...")
Base.metadata.create_all(bind=engine)

def get_anomaly_metrics(db, product_id: str, current_price: float):
    """Computes statistical delta metrics using tracking bounds from historical records."""
    history = db.query(PriceHistory).filter(PriceHistory.product_id == product_id).order_by(PriceHistory.timestamp.desc()).all()
    
    if not history:

        return 1.0, 0.0, current_price
        
    prices = [h.price for h in history]
    last_price = prices[0]
    median_price = float(np.median(prices))
    
    price_ratio = current_price / median_price if median_price > 0 else 1.0
    pct_change = (current_price - last_price) / last_price if last_price > 0 else 0.0
    
    return price_ratio, pct_change, median_price

async def consume_events():
    """Infinite loop pulling serialized Protobuf bytes, processing anomaly evaluation, and handling persistence."""
    logger.info(f"Subscribing to streaming data fabrics at topic target '{KAFKA_TOPIC}'...")
    
    consumer = None
    for attempt in range(10):
        try:
            consumer = AIOKafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=CONSUMER_GROUP,
                auto_offset_reset="earliest"
            )
            await consumer.start()
            logger.info("Kafka consumer initialized successfully.")
            break
        except Exception as e:
            logger.warning(f"Kafka engine target broker out-of-bounds (Attempt {attempt + 1}/10): {e}")
            await asyncio.sleep(3)
            
    if not consumer:
        logger.error("Terminal Connection Fault: Kafka unreachable. Shutting down worker.")
        return

    try:
        async for msg in consumer:
            try:
                with SessionLocal() as db:

                    event = PriceEvent()
                    event.ParseFromString(msg.value)
                    
                    logger.info(f"Ingested stream token: [{event.product_id}] -> {event.price} {event.currency}")
                    

                    product = db.query(Product).filter(Product.id == event.product_id).first()
                    if not product:
                        product = Product(
                            id=event.product_id,
                            name=event.name,
                            url=event.url,
                            source=event.source,
                            category="Electronics"
                        )
                        db.add(product)
                        db.commit()
                        logger.info(f"Idempotent validation passed: Registered entry artifact [{event.product_id}]")
                    

                    price_ratio, pct_change, median_price = get_anomaly_metrics(db, event.product_id, event.price)
                    

                    is_anomaly, score = detector.predict(price_ratio, pct_change)
                    
                    if is_anomaly:
                        logger.warning(f"[ANOMALY INFERENCE ALERT] [{event.product_id}] Out-of-bounds pattern detected! "
                                       f"Price: {event.price}, Median: {median_price:.2f}, "
                                       f"Ratio: {price_ratio:.2f}, Delta: {pct_change:+.2%}, Confidence: {score:.4f}")
                    else:
                        logger.info(f"[Metrics Cleared] [{event.product_id}] Verification confirmed normal. "
                                    f"Ratio: {price_ratio:.2f}, Delta: {pct_change:+.2%}")
                    

                    try:
                        ts = datetime.fromisoformat(event.timestamp)
                    except ValueError:
                        ts = datetime.now(timezone.utc)
                    
                    price_entry = PriceHistory(
                        product_id=event.product_id,
                        price=event.price,
                        currency=event.currency,
                        timestamp=ts,
                        is_anomaly=is_anomaly,
                        anomaly_confidence=float(score)
                    )
                    db.add(price_entry)
                    db.commit()
                    
            except Exception as e:
                logger.error(f"Event parsing execution cycle fault encountered: {e}", exc_info=True)
                
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(consume_events())