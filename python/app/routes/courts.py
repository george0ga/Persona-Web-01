from fastapi import APIRouter, Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.utils.logger import logger
from app.schemas.schemas import CourtCheckModel, CourtResponseModel, PersonInitials, CourtVerifyModel
from app.config.settings import settings
from app.handlers.errors import CourtParsingError, CourtConnectionError, ValidationError

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/v1", tags=["courts"])
        
@router.post("/courts/check", response_model=CourtResponseModel)
@limiter.limit(settings.RATE_LIMIT_API)
async def check_courts(data: CourtCheckModel, request: Request):
    """
    Проверка списка адресов судов
    
    Этот эндпоинт принимает список адресов судов и ФИО для проверки наличия дел на указанных судах.
    После валидации данных, задача проверки добавляется в очередь Celery, и возвращается ID задачи для отслеживания статуса.
    
    Args:
        data: Данные для проверки
            - address: Список URL адресов судов для проверки
            - fullname: ФИО для проверки (объект PersonInitials)
    
    Returns:
        CourtResponseModel: Результат проверки с названием суда
        
    Raises:
        HTTPException 422: При ошибках валидации данных
        HTTPException 500: При ошибках проверки
        
    Example:
        ```json
        {
            "address": [
                "https://k-h2.ros.msudrf.ru"
                ],
            "fullname": {
                "surname": "Степаненко",
                "name": "Михаил",
                "patronymic": "Евгеньевич"
            }
        }
        ```
    """
    if isinstance(data.fullname, dict):
        data.fullname = PersonInitials(**data.fullname)
    logger.info(f"Запрос /courts/check для адресов: {data.address}")
    checker = request.app.state.check_service
    try:
        # fullname — это объект PersonInitials, преобразуем в dict для передачи в Celery
        result = checker.check_courts(data.address, data.fullname.model_dump())
        return CourtResponseModel(
            success=True,
            status="queued",
            message="Задача проверки суда добавлена в очередь",
            data={"task_id": result["task_id"]}
        )
    except ValidationError as e:
        logger.warning(f"Ошибка валидации при batch-проверке: {e}")
        raise HTTPException(status_code=422, detail=f"Ошибка валидации: {e.message}")
    except Exception as e:
        logger.exception(f"Неожиданная ошибка при batch-проверке: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@router.post("/courts/verify", response_model=CourtResponseModel)
@limiter.limit(settings.RATE_LIMIT_API) 
async def verify_court(data: CourtVerifyModel, request: Request):
    """
    Проверка и получение названия суда по адресу
    
    Этот эндпоинт проверяет доступность сайта и проверяет поддержку парсинга суда данноого типа, 
    после чего возвращает его название для дальнейшего использования в фронте.
    
    Args:
        data: Данные для проверки
            - address: URL адрес(а) суда для проверки
    
    Returns:
        CourtResponseModel: Результат проверки с названием суда
        
    Raises:
        HTTPException 422: При ошибках валидации данных
        HTTPException 500: При ошибках проверки
        
    Example:
        ```json
        {
          "address": "http://court.ru"
        }
        ```
    """
    logger.info(f" Запрос /verify/court для адреса: {data.address}")
    checker = request.app.state.check_service  
    
    try:
        result = checker.verify_and_get_court(data.address)

        return CourtResponseModel(
            success=True,
            status="queued",
            message="Задача проверки адреса добавлена в очередь",
            data={"task_id": result["task_id"]}
        )
    except ValidationError as e:
        logger.warning(f" Ошибка валидации при проверке адреса: {e}")
        raise HTTPException(status_code=422, detail=f"Ошибка валидации: {e.message}")
    except CourtConnectionError as e:
        logger.error(f" Ошибка подключения к суду {e.court_url}: {e}")
        raise HTTPException(status_code=503, detail=f"Ошибка подключения к суду: {e.message}")
    except Exception as e:
        logger.exception(f" Неожиданная ошибка при проверке адреса: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")