from app.celery.celery_app import celery_app
from app.parsers.courts.core import parse_courts
from app.parsers.courts.utils import get_court_info
from app.utils.logger import logger
from app.schemas.schemas import PersonInitials

@celery_app.task(bind=True, name="check_court")
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
        result = parse_courts(address, fullname, set_status, headless=False)
        return {"address": address, "result": result, "status": "success"}
    except Exception as e:
        return {"address": address, "error": str(e), "status": "error"}

@celery_app.task(bind=True, name="verify_court")
def verify_court_task(self, address: str):
    """
    Задача для проверки и получения названия суда
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Проверяем адрес суда...'}
        )
        
        court_info = get_court_info(address,None)
        court_name = court_info.name
        if isinstance(court_name, str):
            result = court_name.capitalize()
        else:
            result = "Не удалось получить название суда"
            logger.info(f"[Celery] Задача {self.request.id} завершена с ошибкой")
            return {
            'status': 'error',
            'result': result,
            'task_id': self.request.id
        }

        logger.info(f"[Celery] Задача {self.request.id} завершена успешно")
        return {
            'status': 'success',
            'result': result,
            'task_id': self.request.id
        }
        
    except Exception as e:
        logger.error(f"[Celery] Ошибка в задаче {self.request.id}: {e}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise