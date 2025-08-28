import time

from bs4 import BeautifulSoup, Tag
from dataclasses import dataclass
from typing import Optional, Union
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from app.services.browser import create_driver
from app.utils.logger import logger

MAX_RETRIES = 15
MAX_RETRIES_UNAVAILABLE = 3
RETRY_DELAY = 3

@dataclass
class CourtInfo:
    supported: bool
    type: Optional[str]
    name: Optional[str]
    error: Optional[str] = None

def timing_decorator(func):
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        log_line = f"{func.__name__} заняла {elapsed:.2f} сек\n"
        with open("timing.log", "a", encoding="utf-8") as f:
            f.write(log_line)
        return result
    return wrapper

@timing_decorator
def check_unexpected_alert(driver,):
    try:
        alert = driver.switch_to.alert
        text = ""
        try:
            text = alert.text.strip()
        except Exception:
            text = ""
        try:
            alert.accept()
        except Exception:
            try:
                alert.dismiss()
            except Exception:
                pass
        logger.warning(f"[check_unexpected_alert] Закрыт alert: {text!r}")
        logger.info("[check_unexpected_alert] Страница обновлена после alert")
    except Exception as e:
        logger.success(f"[check_unexpected_alert] alert не появился: {e}")
        return

@timing_decorator
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

@timing_decorator
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

@timing_decorator
def check_unavailable_message(driver):
    logger.info(f"[check_unavailable_message] Проверка сообщения об отсутствии данных.")
    try:
        for attempt in range(MAX_RETRIES_UNAVAILABLE):
            message = driver.find_element((By.XPATH, "//*[contains(text(),'Информация временно недоступна')]"))
            if not message:
                logger.success(f"[check_unavailable_message] Сообщение об отсутствии данных не обнаружено.")
                return
            logger.warning(f"[check_unavailable_message] Сообщение об отсутствии данных обнаружено.")
            time.sleep(RETRY_DELAY)
            driver.refresh()
        raise RuntimeError(f"[check_unavailable_message] Судебные делопроизводства в данном суде недоступны. Проверьте данный адрес позже.")
    except Exception as e:
        logger.success(f"[check_unavailable_message] Сообщение об отсутствии данных не обнаружено.")
        return

@timing_decorator
def make_name_initials(fullname):
    logger.info(f"[make_name_initials] Формирование вариантов ФИО из: {fullname.surname} {fullname.name} {fullname.patronymic}")
    names = []

    try:
        if fullname.name and fullname.patronymic:
            # Иванов Иван Иванович
            full = f"{fullname.surname} {fullname.name} {fullname.patronymic}"
            names.append(full)
            logger.debug(f"[make_name_initials] Добавлен полный формат: {full}")

            # Иванов И. И.
            initials = f"{fullname.surname} {fullname.name[0]}. {fullname.patronymic[0]}. "
            names.append(initials)
            logger.debug(f"[make_name_initials] Добавлены инициалы: {initials}")
            return names
        else:
            if fullname.name:
                # Иванов И
                initials = f"{fullname.surname} {fullname.name[0]} "
                names.append(initials)
                logger.debug(f"[make_name_initials] Добавлен вариант с первой буквой имени: {initials}")

                # Иванов Иван
                full = f"{fullname.surname} {fullname.name}"
                names.append(full)
                logger.debug(f"[make_name_initials] Добавлен вариант с именем без отчества: {full}")
                return names
        # Иванов
        names.append(fullname.surname)
        logger.debug(f"[make_name_initials] Добавлена только фамилия: {fullname.surname}")

        logger.success(f"[make_name_initials] Всего сформировано вариантов: {len(names)}")
        return names

    except Exception as e:
        logger.exception(f"[make_name_initials] Ошибка при формировании ФИО: {e}")
        return [fullname.surname]

@timing_decorator
def verify_page(driver,):
    try:
        check_unexpected_alert(driver)
        check_unavailable_message(driver)
        check_502(driver)
        check_503(driver)
    except Exception as e:
        logger.error(f"[verify_page] Ошибка при проверке страницы: {e}")

@timing_decorator
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


def clean_table(html_or_tag: Union[str, Tag]) -> Optional[Tag]:
    # 1) Получаем сам Tag таблицы
    if isinstance(html_or_tag, Tag):
        table = html_or_tag
    else:
        soup = BeautifulSoup(html_or_tag or "", "html.parser")
        table = soup.find("table")
        if table is None:
            return None

    # 2) Функция удаления нежелательных атрибутов
    def strip_attrs(tag: Tag):
        for attr in list(tag.attrs):
            if (
                attr == "style"
                or attr.startswith("on")           # onmouseover/onclick/...
                or attr in ("width", "height", "border",
                            "cellpadding", "cellspacing",
                            "align", "valign", "color")
            ):
                del tag[attr]

    # чистим саму таблицу и всех потомков
    strip_attrs(table)
    for el in table.find_all(True):
        strip_attrs(el)

    return table

@timing_decorator
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

@timing_decorator
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

@timing_decorator
def get_court_info(address,driver):
    need_to_close = False
    if driver is None:
        need_to_close = True
        driver = create_driver("eager", headless=True)
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

