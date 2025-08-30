from celery import group
from app.celery.tasks import verify_court_task, check_court_task
from app.utils.logger import logger
from app.parsers.courts.core import parse_courts
from app.config.settings import settings

class CheckService():
    def __init__(self, headless=settings.HEADLESS):
        self.headless_mode = headless
    
    def check_courts(self, addresses, fullname_data):
        """
        Проверяет список адресов судов.
        """
        try:
            task = group(check_court_task.s(address, fullname_data) for address in addresses)
            async_result = task.apply_async()
            async_result.save()
            return {
                'task_id': async_result.id,
                'status': 'queued',
                'message': 'Задача проверки адреса добавлена в очередь'
            }
        except Exception as e:
            logger.exception(f"[Celery] Ошибка проверки адресов: {e}")
            raise Exception(f"Ошибка проверки адресов: {e}")
        except Exception as e:
            logger.exception(f"[Celery] Ошибка отправки batch-задачи: {e}")
            raise Exception(f"Ошибка отправки batch-задачи: {e}")

    def check_courts_no_queue(self, addresses, fullname_data):
        """
        Проверяет список адресов судов без отправки в очередь
        """
        try:
            results = {}
            for address in addresses:
                court_result = parse_courts(address, fullname_data, headless=settings.HEADLESS)
                results[address] = court_result
            logger.info(f"[Celery] Batch-задача проверки адресов завершена")
            return {
                'status': 'success',
                'results': results
            }
        except Exception as e:
            logger.exception(f"[Celery] Ошибка проверки адресов: {e}")
            raise Exception(f"Ошибка проверки адресов: {e}")
        except Exception as e:
            logger.exception(f"[Celery] Ошибка отправки batch-задачи: {e}")
            raise Exception(f"Ошибка отправки batch-задачи: {e}")

    def verify_and_get_court(self, address):
        """
        Отправляет задачу проверки адреса суда в очередь
        """
        try:
            task = verify_court_task.delay(address)
            
            logger.info(f"[Celery] Задача проверки адреса отправлена: {task.id}")
            return {
                'task_id': task.id,
                'status': 'queued',
                'message': 'Задача проверки адреса добавлена в очередь'
            }
            
        except Exception as e:
            logger.exception(f"[Celery] Ошибка отправки задачи проверки адреса: {e}")
            raise Exception(f"Ошибка отправки задачи: {e}")