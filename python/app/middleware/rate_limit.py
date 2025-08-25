# middleware/rate_limit.py
from fastapi import FastAPI, Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from app.utils.logger import logger
from app.config.settings import settings

limiter = Limiter(key_func=get_remote_address)

def setup_rate_limit_middleware(app: FastAPI):
    """Настройка rate limiting middleware"""
    
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
        """Обработчик превышения лимита запросов"""
        logger.warning(f"Превышен лимит запросов с IP: {request.client.host}")
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "status": "rate_limit_exceeded",
                "message": "Слишком много запросов. Попробуйте позже.",
                "retry_after": getattr(exc, 'retry_after', None)
            }
        )
    
    # НЕ добавляем глобальный middleware - только обработчик ошибок
    # Rate limiting будет работать через декораторы @limiter.limit() на эндпоинтах