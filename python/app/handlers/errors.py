# handlers/errors.py
import os
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from app.utils.logger import logger

# Кастомные исключения (добавляем в начало файла)
class CourtParsingError(Exception):
    """Ошибка при парсинге судов"""
    def __init__(self, message: str, court_url: str = None, details: str = None):
        logger.error(f"Ошибка при парсинге судов:{message}")
        self.message = message
        self.court_url = court_url
        self.details = details
        super().__init__(self.message)

class CaptchaError(Exception):
    """Ошибка при решении капчи"""
    def __init__(self, message: str, attempts: int = 0, captcha_type: str = None):
        logger.error(f"Ошибка при решении капчи:")
        self.message = message
        self.attempts = attempts
        self.captcha_type = captcha_type
        super().__init__(self.message)

class CourtConnectionError(Exception):
    """Ошибка подключения к сайту суда"""
    def __init__(self, message: str, court_url: str = None, status_code: int = None):
        logger.error(f"Ошибка подключения к сайту суда:{message}")
        self.message = message
        self.court_url = court_url
        self.status_code = status_code
        super().__init__(self.message)

class ValidationError(Exception):
    """Ошибка валидации данных"""
    def __init__(self, message: str, field: str = None, value: str = None):
        logger.error(f"Ошибка валидации данных:{message}")
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)

class RateLimitError(Exception):
    """Ошибка превышения лимита запросов"""
    def __init__(self, message: str, retry_after: int = None):
        logger.error(f"Ошибка превышения лимита запросов:{message}")
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)

def setup_error_handlers(app):
    """Настройка глобальных обработчиков ошибок"""
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Глобальный обработчик всех необработанных исключений"""
        
        logger.exception(f"""
        КРИТИЧЕСКАЯ ОШИБКА!
        URL: {request.url.path}
        Метод: {request.method}
        Ошибка: {exc}
        Тип ошибки: {type(exc).__name__}
        """)
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "status": "server_error",
                "message": "Внутренняя ошибка сервера",
                "detail": str(exc) if os.getenv("DEBUG") == "1" else "Ошибка обработки запроса"
            }
        )

    @app.exception_handler(ValueError)
    async def validation_exception_handler(request: Request, exc: ValueError):
        """Обработчик ошибок валидации"""
        logger.warning(f"Ошибка валидации в {request.url.path}: {exc}")
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "status": "validation_error",
                "message": "Ошибка валидации данных",
                "detail": str(exc)
            }
        )

    # Добавляем обработчики для кастомных исключений
    @app.exception_handler(CourtParsingError)
    async def court_parsing_exception_handler(request: Request, exc: CourtParsingError):
        """Обработчик ошибок парсинга судов"""
        logger.error(f"Ошибка парсинга суда {exc.court_url}: {exc.message}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "status": "parsing_error",
                "message": "Ошибка при парсинге суда",
                "detail": exc.message,
                "court_url": exc.court_url
            }
        )

    @app.exception_handler(CaptchaError)
    async def captcha_exception_handler(request: Request, exc: CaptchaError):
        """Обработчик ошибок капчи"""
        logger.error(f"Ошибка капчи (попыток: {exc.attempts}): {exc.message}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "status": "captcha_error",
                "message": "Ошибка при решении капчи",
                "detail": exc.message,
                "attempts": exc.attempts
            }
        )

    @app.exception_handler(CourtConnectionError)
    async def court_connection_exception_handler(request: Request, exc: CourtConnectionError):
        """Обработчик ошибок подключения к судам"""
        logger.error(f"Ошибка подключения к суду {exc.court_url}: {exc.message}")
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "status": "connection_error",
                "message": "Ошибка подключения к суду",
                "detail": exc.message,
                "court_url": exc.court_url
            }
        )

    @app.exception_handler(ValidationError)
    async def custom_validation_exception_handler(request: Request, exc: ValidationError):
        """Обработчик кастомных ошибок валидации"""
        logger.warning(f"Ошибка валидации поля '{exc.field}' в {request.url.path}: {exc.message}")
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "status": "validation_error",
                "message": "Ошибка валидации данных",
                "detail": exc.message,
                "field": exc.field
            }
        )

    @app.exception_handler(RateLimitError)
    async def rate_limit_exception_handler(request: Request, exc: RateLimitError):
        """Обработчик ошибок превышения лимита"""
        logger.warning(f"Превышен лимит запросов: {exc.message}")
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "status": "rate_limit_error",
                "message": "Превышен лимит запросов",
                "detail": exc.message,
                "retry_after": exc.retry_after
            }
        )