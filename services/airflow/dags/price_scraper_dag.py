import os
import logging
from datetime import datetime, timedelta
import requests

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator

except ImportError:

    class DAG:
        def __init__(self, *args, **kwargs): pass
    class PythonOperator:
        def __init__(self, *args, **kwargs): pass

# Initialize structural logging matching our core pipeline standard definitions
logger = logging.getLogger("airflow.task")

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://backend:8000")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(seconds=30),
}

dag = DAG(
    "price_intelligence_crawler",
    default_args=default_args,
    description="Automated pricing scraper scheduler triggering Celery execution contexts",
    schedule=timedelta(minutes=1),  # Using Airflow 2.x 'schedule'
    catchup=False,
)

def trigger_scraper_for_product(product_id: str, **kwargs):
    """Dispatches a POST request to the API gateway to enqueue a background Celery task node."""
    url = f"{BACKEND_API_URL}/scrape"
    params = {"product_id": product_id}
    logger.info(f"Dispatching ingress worker trigger request to {url} for target product: {product_id}...")
    
    try:
        response = requests.post(url, params=params, timeout=15)
        if response.status_code == 200:
            logger.info(f"Task ingestion verified successfully. Response schema: {response.json()}")
        else:
            raise Exception(f"API Gateway rejected task invocation. Status: {response.status_code}, Payload: {response.text}")
    except requests.exceptions.RequestException as req_err:
        raise Exception(f"Network transport fault communicating with backend gateway node: {req_err}")

PRODUCTS = ["iphone-15", "macbook-pro", "playstation-5", "airpods-pro"]

for product in PRODUCTS:
    task_safe_id = product.replace("-", "_")
    task = PythonOperator(
        task_id=f"trigger_scrape_{task_safe_id}",
        python_callable=trigger_scraper_for_product,
        op_kwargs={"product_id": product},
        dag=dag,
    )