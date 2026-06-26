import asyncio
import os
import logging
import re
from datetime import datetime, timezone
import aiohttp
from aiokafka import AIOKafkaProducer
from services.scraper.main import celery_app
from services.shared.price_event_pb2 import PriceEvent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "price-events")

_kafka_producer = None

async def get_kafka_producer():
    """Returns a shared, active instance of the async Kafka producer."""
    global _kafka_producer
    if _kafka_producer is None:
        logger.info(f"Initializing persistent Kafka producer targeting {KAFKA_BOOTSTRAP_SERVERS}...")
        _kafka_producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        await _kafka_producer.start()
    return _kafka_producer

async def send_to_kafka(event_bytes: bytes):
    """Publishes serialized Protobuf bytes to the configured Kafka topic."""
    retries = 3
    for attempt in range(retries):
        try:
            producer = await get_kafka_producer()
            await producer.send_and_wait(KAFKA_TOPIC, event_bytes)
            logger.info(f"Successfully published price event bytes to topic '{KAFKA_TOPIC}'")
            return
        except Exception as e:
            logger.warning(f"Kafka delivery attempt {attempt + 1}/{retries} failed: {e}")
            if attempt == retries - 1:
                raise e
            await asyncio.sleep(2)

async def scrape_product_async(url: str, product_id: str):
    """Asynchronously dispatches HTTP requests, extracts data, and encodes to protobuf."""
    logger.info(f"Executing async fetch engine for product '{product_id}' -> URL: {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, timeout=10) as response:
            if response.status != 200:
                raise Exception(f"HTTP Target error: Remote server returned status {response.status}")
            
            data = None
            try:
                # Primary strategy: Attempt to parse JSON response directly
                data = await response.json()
            except Exception:
                # Fallback strategy: Use regex to extract from HTML if JSON parsing fails
                logger.info("Non-JSON endpoint detected. Diverting data extraction to html parsing fallback...")
                html_text = await response.text()
                
                price_match = re.search(r'"price":\s*([\d\.]+)', html_text)
                title_match = re.search(r'<title>(.*?)</title>', html_text)
                
                if price_match and title_match:
                    data = {
                        "id": product_id,
                        "name": title_match.group(1).strip(),
                        "price": float(price_match.group(1)),
                        "currency": "USD",
                        "url": url,
                        "source": "regex-parser"
                    }
            
            if not data:
                raise Exception("Data Extraction Fault: Unable to map structure via JSON or regex configurations.")
            
            # Map parameters into system abstractions
            name = data.get("name", product_id)
            price = float(data.get("price", 0.0))
            currency = data.get("currency", "USD")
            source = data.get("source", "mock-shop")
            timestamp = datetime.now(timezone.utc).isoformat()
            
            logger.info(f"Extracted [Item: {name} | Price: {price} {currency} | Source: {source}]")
            
            event = PriceEvent(
                product_id=product_id,
                name=name,
                price=price,
                currency=currency,
                timestamp=timestamp,
                url=url,
                source=source
            )
            
            event_bytes = event.SerializeToString()
            await send_to_kafka(event_bytes)
            
            return {
                "product_id": product_id,
                "name": name,
                "price": price,
                "currency": currency,
                "timestamp": timestamp,
                "success": True
            }

@celery_app.task(name="tasks.scrape_product", bind=True, max_retries=3)
def scrape_product(self, url: str, product_id: str):
    """Synchronous Celery wrapper task driving our underlying async IO loop structures."""
    logger.info(f"Celery worker accepted scraping request routing for Product: {product_id}")
    try:
        return asyncio.run(scrape_product_async(url, product_id))
    except Exception as exc:
        logger.error(f"Scraping processing cycle failed for target '{product_id}': {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries + 5)