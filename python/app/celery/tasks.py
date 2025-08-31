from celery import shared_task
from app.celery.celery_app import celery_app
from app.parsers.courts.core import parse_courts
from app.parsers.courts.utils import get_court_info
from app.utils.logger import logger
from app.schemas.schemas import PersonInitials
from app.config.settings import settings
from app.metrics.redis_client import (increment_court_check_size, 
                                      decrement_court_check_size,
                                      increment_court_verify_size,
                                      decrement_court_verify_size)

@celery_app.task(queue='court_checks', bind=True, name="check_court")
def check_court_task(self, address: str, fullname_data: dict):
    """
    Задача для проверки одного суда.
    """
    def set_status(text, court_name):
        self.update_state(
            state='PROGRESS',
            meta={'status': text, 'court_name': court_name}
        )
    try:
        fullname = PersonInitials(**fullname_data)
        increment_court_check_size()
        result = parse_courts(address, fullname, set_status, headless=settings.HEADLESS)
        decrement_court_check_size()
        return {"address": address, "result": result, "status": "success"}
    except Exception as e:
        decrement_court_check_size()
        return {"address": address, "error": str(e), "status": "error"}

@celery_app.task(queue='court_verifications', bind=True, name="verify_court")
def verify_court_task(self, address: str):
    """
    Задача для проверки и получения названия суда
    """
    global celery_verify_courts_queue_size
    try:
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Проверяем адрес суда...'}
        )
        increment_court_verify_size()
        court_info = get_court_info(address,None)
        court_name = court_info.name
        if isinstance(court_name, str):
            result = court_name.capitalize()
        else:
            result = "Не удалось получить название суда"
            logger.info(f"[Celery] Задача {self.request.id} завершена с ошибкой")
            decrement_court_verify_size()
            return {
            'status': 'error',
            'result': result,
            'task_id': self.request.id
        }
        logger.info(f"[Celery] Задача {self.request.id} завершена успешно")
        decrement_court_verify_size()
        return {
            'status': 'success',
            'result': result,
            'task_id': self.request.id
        }
        
    except Exception as e:
        logger.error(f"[Celery] Ошибка в задаче {self.request.id}: {e}")
        decrement_court_verify_size()
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise