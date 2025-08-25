import time

from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from app.services.browser import create_driver
from app.utils.logger import logger

MAX_RETRIES = 15
RETRY_DELAY = 3

@dataclass
class CourtInfo:
    supported: bool
    type: Optional[str]
    name: Optional[str]
    error: Optional[str] = None

def check_503(driver):
    logger.info(f"[check_503] Проверка на ошибку 503.")
    max_retries=15
    retry_delay = 3
    try:
        for attempt in range(max_retries):
            title = driver.title
            page = driver.page_source
            if "503" not in title and "Service Unavailable" not in page:
                logger.info(f"[check_503] Ошибка 503 отсутсвует.")
                return
            print(f"[503 DETECTED] — retry {attempt + 1}/{max_retries}")
            logger.warning(f"[check_503] Обнаружена ошибка 503. Попытка получить доступ {attempt + 1}/{max_retries} ")
            time.sleep(retry_delay)
            driver.refresh()
        raise RuntimeError(f"[503 ERROR] — exceeded {max_retries} retries")
    except RuntimeError as e:
        logger.error(f"[check_503] Ошибка 503. После {max_retries} доступ получить не удалось. ")

def check_502(driver):
    logger.info(f"[check_502] Проверка на ошибку 502.")
    try:
        for attempt in range(MAX_RETRIES):
            title = driver.title
            page = driver.page_source
            if "502" not in title and "Bad Gateway" not in page:
                logger.success(f"[check_502] Ошибка 502 отсутсвует.")
                return
            logger.warning(f"[check_502] Обнаружена ошибка 502. Попытка получить доступ {attempt + 1}/{MAX_RETRIES} ")
            time.sleep(RETRY_DELAY)
            driver.refresh()
        raise RuntimeError(f"[502 ERROR] — exceeded {MAX_RETRIES} retries")
    except RuntimeError as e: 
        logger.error(f"[check_502] Ошибка 502. После {MAX_RETRIES} доступ получить не удалось. ")

def verify_page(driver):
    check_502(driver)
    check_503(driver)

def merge_html_tables(html_list):
    logger.info(f"[merge_html_tables] Начато объединение таблиц.")
    if not html_list:
        logger.info(f"[merge_html_tables] Не данных для заполнения таблицы.")
        return "<div class='placeholder'>Нет данных</div>"

    soup = BeautifulSoup(html_list[0], "html.parser")
    base_table = soup.find("table")

    if base_table is None:
        # Если нет таблицы, просто объединяем текст заглушек
        return "".join(html_list)

    base_body = base_table.find("tbody")

    for html in html_list[1:]:
        temp_soup = BeautifulSoup(html, "html.parser")
        table = temp_soup.find("table")
        if not table:
            continue
        body = table.find("tbody")
        if not body:
            continue
        for row in body.find_all("tr"):
            base_body.append(row)

    return str(base_table)

def get_court_type(driver, address):
    logger.info(f"[get_court_type] Определение типа суда по адресу: {address}")
    driver.get(address)
    verify_page(driver)
    try:
        # Ждём появления любого из двух элементов
        WebDriverWait(driver, 15).until(
            lambda d: d.find_elements(By.ID, "court_name") or d.find_elements(By.CLASS_NAME, "header__middle")
        )
        if driver.find_elements(By.ID, "court_name"):
            return "blue"
        if driver.find_elements(By.CLASS_NAME, "header__middle"):
            return "yellow"
    except Exception as e:
        logger.warning(f"[get_court_type] Не удалось определить тип суда: {e}")

    return "unsupported"

def get_court_name(court_type,driver):
    logger.info(f"[get_court_name] Получение названия суда")
    verify_page(driver)
    try:
        WebDriverWait(driver, 15).until(
            lambda d: d.find_elements(By.ID, "court_name") or d.find_elements(By.CLASS_NAME, "header__middle")
        )
        if court_type == "blue":
            elements = driver.find_elements(By.ID, "court_name")
            if elements:
                name = elements[0].text.strip()
                logger.success(f"[get_court_name] Название суда (blue): {name}")
                return name
        if court_type == "yellow":
            elements = driver.find_elements(By.CLASS_NAME, "heading_title")
            if elements:
                name = elements[0].text.strip()
                logger.success(f"[get_court_name] Название суда (yellow): {name}")
                return name
        logger.error(f"[get_court_name] Не удалось определить название суда! Cайт не поддерживается или произошла ошибка")
        return "unsupported"
    except Exception as e:
        logger.error(f"[get_court_name] Ошибка при получении названия суда: {e}")
        return "unsupported"

def get_court_info(address,driver):
    need_to_close = False
    if driver is None:
        need_to_close = True
        driver = create_driver("eager", headless=False)
    try:
        try:
            driver.get(address)
            verify_page(driver)
        except Exception as e:
            logger.warning(f"[get_court_info] Не удалось открыть сайт: {e}")
            return CourtInfo(supported=False)

        court_type = get_court_type(driver, address)
        court_name = get_court_name(court_type, driver)
        if court_type == "unsupported" or court_name == "unsupported":
            return CourtInfo(supported=False, type=None, name=None, error="Сайт не поддерживается")
        return CourtInfo(supported=True, type=court_type, name=court_name)
    except Exception as e:
        logger.exception(f"[get_court_info] Ошибка: {e}")
        return CourtInfo(supported=False, error=str(e))
    finally:
        if need_to_close:
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"[get_court_info] Ошибка при закрытии драйвера: {e}")