# routes/metrics.py
"""Эндпоинт для метрик Prometheus (для создания графиков)"""
from fastapi import APIRouter, Request
from fastapi.responses import Response
from prometheus_client import  CONTENT_TYPE_LATEST
from app.config.settings import settings
from app.metrics import get_metrics_response
router = APIRouter(prefix="/api/v1",tags=["metrics"])

@router.get("/metrics")
async def metrics_endpoint(request: Request):
    """
    Эндпоинт для метрик Prometheus
    
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
    return get_metrics_response()