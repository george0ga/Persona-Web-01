from celery import Celery
from app.config.settings import settings
from kombu import Queue

# Создаем экземпляр Celery
celery_app = Celery(
    "courts_parser",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.celery.tasks']  # Модуль с задачами
)

celery_app.conf.task_queues = (
    Queue('court_checks'),
    Queue('court_verifications'),
)

# Конфигурация Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=10 * 60,  # 10 минут на задачу
    task_soft_time_limit=6 * 60,  # 6 минут мягкий лимит
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

