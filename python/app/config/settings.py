# config/settings.py
import os
from typing import List

class Settings:
    # API настройки
    API_TITLE = "Persona API"
    API_DESCRIPTION = "API для парсинга веб-ресурсов"
    API_VERSION = "1.0.0"
    
    # CORS настройки
    CORS_ORIGINS: List[str] = [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "null"  # разрешить запросы с file://
    ]
    CORS_METHODS: List[str] = ["GET", "POST"]
    CORS_HEADERS: List[str] = ["Content-Type", "Authorization"]
    CORS_CREDENTIALS: bool = False
    CORS_MAX_AGE: int = 3600
    
    # Health check настройки
    ALLOWED_HEALTH_IPS: List[str] = [
        "127.0.0.1",        # IPv4 localhost
        "::1",               # IPv6 localhost
        "172.16.0.0/12",    # Docker/Kubernetes
        "192.168.0.0/16",   # Локальная сеть
    ]
    
    # Rate limiting
    RATE_LIMIT_DEFAULT = "10/minute"
    RATE_LIMIT_HEALTH = "30/minute"
    RATE_LIMIT_API = "5/minute"
    
    # Сервер настройки
    HOST = "0.0.0.0"
    PORT = 8000
    DEBUG = os.getenv("DEBUG", "0") == "1"

    # Redis настройки
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")

    # Celery настройки
    CELERY_BROKER_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    CELERY_RESULT_BACKEND: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    CELERY_RESULT_EXPIRES = 3600

settings = Settings()