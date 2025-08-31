import asyncio
import prometheus_client
from app.metrics.redis_client import get_queue_size_redis,reset_metrics_timer

from app.utils.logger import logger

redis_queue_size = prometheus_client.Gauge(
    'queue_size',
    'Current size of the task queue',
)

async def monitor_queue_size():
    while True:
        try:
            size_redis_courts = get_queue_size_redis("court_checks")
            redis_queue_size.set(size_redis_courts)
        except Exception as e:
            logger.error(f"Ошибка при получении размера очереди: {e}")
            redis_queue_size.set(-1) 
        await asyncio.sleep(3)

async def start_queue_monitor():
    asyncio.create_task(monitor_queue_size())

async def start_metrics():
    await start_queue_monitor()
    asyncio.create_task(reset_metrics_timer(600))  # Сброс каждые 600 секунд