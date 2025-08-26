from app.services.browser import create_driver
from app.parsers.courts.blue import parse_court_blue
from app.parsers.courts.yellow import parse_court_yellow
from app.parsers.courts.utils import get_court_info
from app.utils.logger import logger
from app.schemas.schemas import PersonInitials 

def parse_courts(address,fullname,set_status,headless=False):
    if isinstance(fullname, dict):
        fullname = PersonInitials(**fullname)
    driver = create_driver("eager", headless)
    try:
        court_info = get_court_info(address,driver)
        court_type = court_info.type
        logger.info(f"[parse_courts] [{address}] Тип суда: {court_type}")
        if court_type == "blue":
            return parse_court_blue(driver, address,court_info.name, fullname,set_status)
        elif court_type == "yellow":
            return parse_court_yellow(driver, address,court_info.name, fullname,set_status)
        else:
            return {f"Сайт {address}": {"__error__": "Сайт не поддерживается"}}
    except Exception as e:
        logger.exception(f"[PROCESS ERROR] {address}: {e}")
        return {f"Сайт {address}": {"__error__": f"Ошибка выполнения проверки: {e}"}}
    finally:
        driver.quit()
        logger.debug(f"[DRIVER] Завершение драйвера для {address}")