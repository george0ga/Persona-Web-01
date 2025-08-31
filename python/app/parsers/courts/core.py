import time

from app.services.browser import create_driver
from app.parsers.courts.blue import parse_court_blue
from app.parsers.courts.yellow import parse_court_yellow
from app.parsers.courts.utils import get_court_info
from app.utils.logger import logger
from app.schemas.schemas import PersonInitials 
from app.config.settings import settings
from app.metrics.redis_client import set_court_last_check_time

def parse_courts(address,fullname,set_status,headless=settings.HEADLESS):
    if isinstance(fullname, dict):
        fullname = PersonInitials(**fullname)
    driver = create_driver("eager", headless)
    try:
        court_info = get_court_info(address,driver)
        court_type = court_info.type
        logger.info(f"[parse_courts] [{address}] Тип суда: {court_type}")
        start_time = time.monotonic()
        if court_type == "blue":
            result = parse_court_blue(driver, address,court_info.name, fullname,set_status)
            set_court_last_check_time(court_type, time.monotonic() - start_time)
            return result
        elif court_type == "yellow":
            result = parse_court_yellow(driver, address,court_info.name, fullname,set_status)
            set_court_last_check_time(court_type, time.monotonic() - start_time)
            return result
        else:
            return {f"Сайт {address}": {"__error__": "Сайт не поддерживается"}}
    except Exception as e:
        logger.exception(f"[PROCESS ERROR] {address}: {e}")
        return {f"Сайт {address}": {"__error__": f"Ошибка выполнения проверки: {e}"}}
    finally:
        driver.quit()
        logger.debug(f"[DRIVER] Завершение драйвера для {address}")