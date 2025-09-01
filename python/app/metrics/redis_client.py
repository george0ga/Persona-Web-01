import asyncio
import redis
import os
from app.config.settings import settings
from app.utils.logger import logger

r = redis.Redis.from_url(
    f"{settings.REDIS_URL}/{settings.REDIS_DB}",
    decode_responses=True,
)

KEY_QUEUE_DEPTH_CHECK  = "metrics:queues:check_court:depth"
KEY_QUEUE_DEPTH_VERIFY = "metrics:queues:verify_court:depth"

KEY_RUNNING_CHECK  = "metrics:running:check_court"
KEY_RUNNING_VERIFY = "metrics:running:verify_court"

def get_queue_size_redis(queue_name):
    return r.llen(queue_name)

def decrement_court_check_size():
    r.decrby("celery_court_check_size", 1)

def increment_court_check_size():
    r.incrby("celery_court_check_size", 1)

def get_court_check_size():
    return r.get("celery_court_check_size")

def decrement_court_verify_size():
    r.decrby("celery_court_verify_size", 1)

def increment_court_verify_size():
    r.incrby("celery_court_verify_size", 1)

def get_court_verify_size():
    return r.get("celery_court_verify_size")

def set_court_last_check_time(court_type, time):
    r.set(f"celery_court_last_check_time_{court_type}", time)

def get_court_last_check_time(court_type):
    return r.get(f"celery_court_last_check_time_{court_type}")

def is_queue_empty():
    court_check_size = get_court_check_size()
    court_verify_size = get_court_verify_size()

    # Безопасное преобразование
    court_check_size = int(court_check_size) if court_check_size is not None else 0
    court_verify_size = int(court_verify_size) if court_verify_size is not None else 0
    return (court_check_size == 0 and court_verify_size == 0)

def reset_check_time_metrics():
    if (is_queue_empty()):
        logger.info("Очереди пусты, сбрасываем метрики времени проверок судов")
        r.set("celery_court_last_check_time_blue", 0)
        r.set("celery_court_last_check_time_yellow", 0)

async def reset_metrics_timer(timer):
    while True:
        await asyncio.sleep(timer)
        reset_check_time_metrics()
        logger.info("Метрики времени проверок судов сброшены")