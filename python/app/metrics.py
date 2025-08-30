# metrics.py
"""Система метрик Prometheus для создания графиков и мониторинга"""
import asyncio
from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
import time
from typing import Dict, Any, Callable, Awaitable
from functools import wraps
from app.utils.logger import logger

# ===== МЕТРИКИ ДЛЯ ГРАФИКОВ =====

# 1. HTTP ЗАПРОСЫ (график количества запросов по времени)
HTTP_REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status', 'client_ip']
)

# 2. ВРЕМЯ ВЫПОЛНЕНИЯ (график производительности)
HTTP_REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0]
)

# 3. ПАРСИНГ СУДОВ (график успешности)
COURT_PARSING_TOTAL = Counter(
    'court_parsing_total',
    'Total number of court parsing attempts',
    ['court_type', 'status', 'parsing_method']
)

# 4. ВРЕМЯ ПАРСИНГА (график производительности парсинга)
COURT_PARSING_DURATION = Histogram(
    'court_parsing_duration_seconds',
    'Court parsing duration in seconds',
    ['court_type', 'parsing_method'],
    buckets=[1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0]
)

# 5. КАПЧА (график успешности решения)
CAPTCHA_SOLVING_TOTAL = Counter(
    'captcha_solving_total',
    'Total number of captcha solving attempts',
    ['status', 'captcha_type', 'solving_method']
)

# 6. ВРЕМЯ РЕШЕНИЯ КАПЧИ (график производительности)
CAPTCHA_SOLVING_DURATION = Histogram(
    'captcha_solving_duration_seconds',
    'Captcha solving duration in seconds',
    ['captcha_type', 'solving_method']
)

# 7. АКТИВНЫЕ ЗАДАЧИ (график нагрузки)
ACTIVE_PARSING_TASKS = Gauge(
    'active_parsing_tasks',
    'Number of currently active parsing tasks',
    ['status']
)

# 8. РАЗМЕР ОЧЕРЕДИ (график очереди)
TASK_QUEUE_SIZE = Gauge(
    'task_queue_size',
    'Current size of the task queue'
)

# 9. ИСПОЛЬЗОВАНИЕ ПАМЯТИ (график ресурсов)
MEMORY_USAGE_BYTES = Gauge(
    'memory_usage_bytes',
    'Current memory usage in bytes'
)

# 10. ВРЕМЯ РАБОТЫ (график uptime)
APPLICATION_UPTIME_SECONDS = Gauge(
    'application_uptime_seconds',
    'Application uptime in seconds'
)

# 12. ОШИБКИ (график ошибок по типам)
ERRORS_TOTAL = Counter(
    'errors_total',
    'Total number of errors',
    ['error_type', 'endpoint', 'status_code']
)

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

def get_metrics():
    """Получить все метрики в формате Prometheus"""
    return generate_latest()

def get_metrics_response() -> Response:
    """Получить метрики в виде FastAPI Response"""
    return Response(
        content=get_metrics(),
        media_type=CONTENT_TYPE_LATEST
    )

# ===== ДЕКОРАТОРЫ ДЛЯ АВТОМАТИЧЕСКОГО СБОРА МЕТРИК =====

def track_http_metrics():
    """Декоратор для отслеживания HTTP метрик (для графиков)"""
    def decorator(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger.info(f"🔍 Декоратор track_http_metrics вызван для функции {func.__name__}")
            
            request: Request | None = None

            # FastAPI обычно кладёт request в kwargs
            if "request" in kwargs and isinstance(kwargs["request"], Request):
                request = kwargs["request"]
            else:
                # fallback: ищем среди args
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if request is None:
                # если совсем не нашли — просто выполняем функцию без метрик
                return await func(*args, **kwargs)
            
            logger.info(f" найден: {request.method} {request.url.path}")
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # Успешный запрос - метрики для графиков
                duration = time.time() - start_time
                
                logger.info(f"📊 Обновляем метрики для {request.method} {request.url.path}")
                
                # 1. Счетчик запросов (график количества)
                HTTP_REQUESTS_TOTAL.labels(
                    method=request.method,
                    endpoint=request.url.path,
                    status=200,
                    client_ip=request.client.host
                ).inc()
                
                # 2. Время выполнения (график производительности)
                HTTP_REQUEST_DURATION.labels(
                    method=request.method,
                    endpoint=request.url.path
                ).observe(duration)
                
                logger.info(f" Метрики обновлены для {request.method} {request.url.path}")
                return result
                
            except Exception as e:
                # Ошибка - метрики для графиков ошибок
                duration = time.time() - start_time
                status = getattr(e, 'status_code', 500)
                
                logger.info(f" Ошибка в {request.method} {request.url.path}, обновляем метрики ошибок")
                
                # 1. Счетчик ошибок (график ошибок)
                HTTP_REQUESTS_TOTAL.labels(
                    method=request.method,
                    endpoint=request.url.path,
                    status=status,
                    client_ip=request.client.host
                ).inc()
                
                # 2. Время выполнения (даже при ошибке)
                HTTP_REQUEST_DURATION.labels(
                    method=request.method,
                    endpoint=request.url.path
                ).observe(duration)
                
                # 3. Счетчик ошибок по типам (график типов ошибок)
                ERRORS_TOTAL.labels(
                    error_type=type(e).__name__,
                    endpoint=request.url.path,
                    status_code=status
                ).inc()
                
                logger.info(f" Метрики ошибок обновлены для {request.method} {request.url.path}")
                raise
                
        return wrapper
    return decorator

def track_parsing_metrics(court_type: str, parsing_method: str):
    """Декоратор для отслеживания метрик парсинга (для графиков)"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # Успешный парсинг - метрики для графиков
                duration = time.time() - start_time
                
                # 1. Счетчик успешных парсингов (график успешности)
                COURT_PARSING_TOTAL.labels(
                    court_type=court_type,
                    status="success",
                    parsing_method=parsing_method
                ).inc()
                
                # 2. Время парсинга (график производительности)
                COURT_PARSING_DURATION.labels(
                    court_type=court_type,
                    parsing_method=parsing_method
                ).observe(duration)
                
                return result
                
            except Exception as e:
                # Ошибка парсинга - метрики для графиков ошибок
                duration = time.time() - start_time
                
                # 1. Счетчик ошибок парсинга (график ошибок)
                COURT_PARSING_TOTAL.labels(
                    court_type=court_type,
                    status="error",
                    parsing_method=parsing_method
                ).inc()
                
                # 2. Время до ошибки (график производительности)
                COURT_PARSING_DURATION.labels(
                    court_type=court_type,
                    parsing_method=parsing_method
                ).observe(duration)
                
                raise
                
        return wrapper
    return decorator

def track_captcha_metrics(captcha_type: str, solving_method: str):
    """Декоратор для отслеживания метрик капчи (для графиков)"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # Успешное решение - метрики для графиков
                duration = time.time() - start_time
                
                # 1. Счетчик успешных решений (график успешности)
                CAPTCHA_SOLVING_TOTAL.labels(
                    status="success",
                    captcha_type=captcha_type,
                    solving_method=solving_method
                ).inc()
                
                # 2. Время решения (график производительности)
                CAPTCHA_SOLVING_DURATION.labels(
                    captcha_type=captcha_type,
                    solving_method=solving_method
                ).observe(duration)
                
                return result
                
            except Exception as e:
                # Ошибка решения - метрики для графиков ошибок
                duration = time.time() - start_time
                
                # 1. Счетчик ошибок решения (график ошибок)
                CAPTCHA_SOLVING_TOTAL.labels(
                    status="error",
                    captcha_type=captcha_type,
                    solving_method=solving_method
                ).inc()
                
                # 2. Время до ошибки (график производительности)
                CAPTCHA_SOLVING_DURATION.labels(
                    captcha_type=captcha_type,
                    solving_method=solving_method
                ).observe(duration)
                
                raise
                
        return wrapper
    return decorator

# ===== ФУНКЦИИ ДЛЯ ОБНОВЛЕНИЯ GAUGE МЕТРИК =====

def update_task_metrics(active_tasks: int, queued_tasks: int):
    """Обновление метрик задач (для графиков нагрузки)"""
    ACTIVE_PARSING_TASKS.labels(status="running").set(active_tasks)
    ACTIVE_PARSING_TASKS.labels(status="queued").set(queued_tasks)
    TASK_QUEUE_SIZE.set(queued_tasks)

def update_memory_metrics():
    """Обновление метрик памяти (для графиков ресурсов)"""
    import psutil
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        MEMORY_USAGE_BYTES.set(memory_info.rss)
    except ImportError:
        # psutil не установлен, используем примерную оценку
        import gc
        gc.collect()
        MEMORY_USAGE_BYTES.set(0)

def update_uptime_metric():
    """Обновление метрики времени работы (для графика uptime)"""
    import time
    start_time = getattr(update_uptime_metric, 'start_time', None)
    if start_time is None:
        start_time = time.time()
        update_uptime_metric.start_time = start_time
    
    uptime = time.time() - start_time
    APPLICATION_UPTIME_SECONDS.set(uptime)

# ===== ИНИЦИАЛИЗАЦИЯ МЕТРИК =====

def initialize_metrics():
    """Инициализация метрик для графиков"""
    # Устанавливаем начальные значения
    APPLICATION_UPTIME_SECONDS.set(0)
    TASK_QUEUE_SIZE.set(0)
    ACTIVE_PARSING_TASKS.labels(status="running").set(0)
    ACTIVE_PARSING_TASKS.labels(status="queued").set(0)
    MEMORY_USAGE_BYTES.set(0)
    
    logger.info("Метрики Prometheus инициализированы для создания графиков")

async def metrics_poller():
        while True:
            update_uptime_metric()
            update_memory_metrics()
            await asyncio.sleep(5)