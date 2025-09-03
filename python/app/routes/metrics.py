import prometheus_client

from fastapi import APIRouter, Request, Response

from app.metrics.redis_client import (get_court_check_size,
                                      get_court_verify_size, get_queue_size_redis,
                                      get_court_last_check_time)

from app.schemas.schemas import QueueSizeResponseModel

router = APIRouter(prefix="/api/v1",tags=["metrics"])

@router.get("/metrics")
async def metrics(request: Request):
    """
    Эндпоинт для метрик Prometheus(WIP)
    
    Возвращает все метрики приложения в формате Prometheus.
    Используется для создания графиков в Grafana, Prometheus UI и других инструментах.
    
    Примеры графиков, которые можно построить:
    - Количество HTTP запросов по времени
    - Время выполнения API эндпоинтов
    - Успешность парсинга судов
    - Производительность решения капчи
    - Нагрузка на систему
    - Ошибки по типам
    """
    return Response(
        content=prometheus_client.generate_latest(), 
        media_type="text/plain; version=0.0.4; charset=utf-8"
        )

@router.get("/metrics/queue_size")
async def get_queue_size(request: Request):
    """
    Эндпоинт для получения размера очереди задач Celery и Redis
    """
    result = {}
    result["redis_courts"] = get_queue_size_redis("court_checks") or 0
    result["redis_verify"] = get_queue_size_redis("court_verifications") or 0
    result["court"] = get_court_check_size() or 0
    result["verify"] = get_court_verify_size() or 0
    result["celery_court_last_check_time_blue"] = float(get_court_last_check_time("blue") or 0.0)
    result["celery_court_last_check_time_yellow"] = float(get_court_last_check_time("yellow") or 0.0)
    return QueueSizeResponseModel(
        redis_check_courts_queue_size=result["redis_courts"],
        redis_verify_courts_queue_size=result["redis_verify"],
        celery_check_courts_queue_size=result["court"],
        celery_verify_courts_queue_size=result["verify"],
        celery_court_last_check_time_blue=result["celery_court_last_check_time_blue"],
        celery_court_last_check_time_yellow=result["celery_court_last_check_time_yellow"]
    )