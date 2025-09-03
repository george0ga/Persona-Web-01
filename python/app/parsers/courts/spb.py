from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

import time

from app.parsers.courts.utils import  make_name_initials, verify_page, wd_safe_click,wd_safe_wait,send_with_delay
from app.utils.logger import logger


def extract_table_html(driver):
    logger.info(f"[extract_table_html] Получение таблицы дел типа rwd-table.")
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "rwd-table")))
    except Exception as e:
        logger.error(f"[extract_table_html] Не удалось загрузить таблицу дел")
        return "<div class='placeholder'>Нет данных</div>"
    soup = BeautifulSoup(driver.page_source, "html.parser")
    table = soup.find("table", class_="rwd-table")
    return str(table) if table else "<div class='placeholder'>Нет данных</div>"

def merge_html_tables(html_list):
    logger.info(f"[merge_html_tables] Начато объединение таблиц rwd-table.")
    if not html_list:
        return "<div class='placeholder'>Нет данных</div>"

    soup = BeautifulSoup(html_list[0], "html.parser")
    base_table = soup.find("table", class_="rwd-table")
    if not base_table:
        return "<div class='placeholder'>Нет данных</div>"
    base_tbody = base_table.find("tbody")
    header_tr = base_tbody.find("tr", recursive=False)
    rows = base_tbody.find_all("tr", recursive=False)[1:] if header_tr else base_tbody.find_all("tr", recursive=False)

    for html in html_list[1:]:
        temp_soup = BeautifulSoup(html, "html.parser")
        table = temp_soup.find("table", class_="rwd-table")
        if not table:
            continue
        tbody = table.find("tbody")
        if not tbody:
            continue
        tr_list = tbody.find_all("tr", recursive=False)
        if tr_list and tr_list[0].find("th"):
            tr_list = tr_list[1:]
        rows.extend(tr_list)

    base_tbody.clear()
    if header_tr:
        base_tbody.append(header_tr)
    for row in rows:
        base_tbody.append(row)

    return str(base_table)

def find_next_btn(driver):
    logger.info(f"[find_next_btn] Поиск кнопки 'Далее'.")
    try:
        next_btn = wd_safe_wait(driver, 10, EC.presence_of_element_located, By.CSS_SELECTOR, "a.pag__next.ng-scope")
        logger.info(f"[find_next_btn] Кнопка 'Далее' найдена.")
        return next_btn
    except Exception as e:
        logger.warning(f"[find_next_btn] Кнопка 'Далее' не найдена.")
        return None

def get_all_cases(driver):
    logger.info(f"[get_all_cases] Парсинг результата.")
    try:
        WebDriverWait(driver, 120).until(lambda d: d.find_elements(By.CLASS_NAME, "ng-binding") or d.find_elements(By.CSS_SELECTOR, 'table.rwd-table tr[ng-if="cases.length == 0"]'))
    except:
        logger.error(f"[get_all_cases] Превышено ожидание ответа от сайта!")
        raise RuntimeError("Превышено ожидание ответа от сайта!")
    no_cases = driver.find_elements(By.CSS_SELECTOR, 'table.rwd-table tr[ng-if="cases.length == 0"]')
    if (no_cases):
        logger.info(f"[get_all_cases] Дела не найдены.")
        return "<div class='placeholder'>Дела не найдены</div>"
    logger.info(f"[get_all_cases] Дела найдены.")
    all_pages = []
    page = extract_table_html(driver)
    all_pages.append(page)
    next_btn = find_next_btn(driver)
    while next_btn != None:
        verify_page(driver)
        try:
            page = extract_table_html(driver)
        except Exception as e:
            logger.error(f"[get_all_cases] Ошибка при получении таблицы категории")
        all_pages.append(page)
        wd_safe_click(driver,10, EC.element_to_be_clickable, next_btn)
        next_btn = find_next_btn(driver)
    return merge_html_tables(all_pages)

def set_date(driver):
    wd_safe_wait(driver,10,EC.presence_of_element_located, By.ID, "id_date_from")
    date_input = driver.find_element(By.ID, "id_date_from")
    send_with_delay(driver, date_input, "01.01.1991")

def parse_court_spb(driver, address,court_name,fullname,set_status):
    court_results = {}
    court_results["Мировые судьи Санкт-Петербурга"] = {}
    names = make_name_initials(fullname)
    link_to_global_search = "https://mirsud.spb.ru/cases/?type=civil&id=&full_name="
    logger.info(f"[parse_court_spb] Начало проверки.")
    set_status(f"Начало проверки",court_name)
    for name_to_check in names:
        court_results["Мировые судьи Санкт-Петербурга"][name_to_check] = {}
        logger.info(f"[parse_court_spb] Проверка доступа к сайту суда: {address}")
        driver.get(link_to_global_search)
        verify_page(driver)
        logger.info(f"[parse_court_spb] Ожидание загрузки элементов на странице")
        wd_safe_wait(driver, 10, EC.presence_of_element_located, By.CLASS_NAME, "cases-list")
        logger.info(f"[parse_court_spb] Элементы на странице загружены")
        logger.info(f"[parse_court_spb] Ожидание загрузки элемента fancy-select")
        wd_safe_wait(driver, 10, EC.presence_of_element_located, By.CLASS_NAME, "fancy-select")
        logger.info(f"[parse_court_spb] Элемент fancy-select загружен")
        logger.info(f"[parse_court_spb] Получение списка опций")
        wd_safe_wait(driver, 10, EC.visibility_of_all_elements_located, By.CSS_SELECTOR, "select#affairs option")
        options = driver.find_elements(By.CSS_SELECTOR, 'select#affairs option')
        logger.info(f"[parse_court_spb] Опции получены: {len(options)} найдено.")
        logger.info(f"[parse_court_spb] Устанавливаю дату.")
        set_date(driver)
        logger.info(f"[parse_court_spb] Дата установлена.")
        logger.info(f"[parse_court_spb] Начинаю перебор категорий.")
        for option in options:
            value = option.get_attribute("data-raw-value") # Получаем значение data-raw-value="..." 
            category = option.text
            logger.info(f"[parse_court_spb] Парсинг категории: {category}")
            set_status(f"Парсинг категории {category} по ФИО: {name_to_check}", court_name)
            option.click()
            wd_safe_click(driver,10, EC.element_to_be_clickable, By.CSS_SELECTOR, ".fancy-select .trigger")
            send_with_delay(driver, driver.find_element(By.ID, "id_full_name"), name_to_check)
            wd_safe_click(driver,10, EC.element_to_be_clickable, By.CSS_SELECTOR, ".button-mobile button[type='submit']")
            court_results["Мировые судьи Санкт-Петербурга"][name_to_check][category] = get_all_cases(driver)
        logger.success(f"[parse_court_blue] Таблица готова.")
        set_status(f"Проверка по ФИО завершена : {name_to_check}",court_name)
    return court_results


if __name__ == "__main__":
    import json
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from fake_useragent import UserAgent
    from app.schemas.schemas import PersonInitials
    def create_driver(page_load_strategy="normal", headless=True):
        user_agent = UserAgent()
        options = webdriver.ChromeOptions()
        options.page_load_strategy = page_load_strategy
        options.add_argument(f"user-agent={user_agent.random}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--log-level=3")
        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
        # Используем webdriver_manager для автоматической загрузки актуального chromedriver
        logger.info(f" Создание Chrome-драйвера (headless={headless}, strategy='{page_load_strategy}')")
        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            logger.success(" Драйвер успешно создан")
            return driver
        except Exception as e:
            logger.exception(f" Ошибка при создании драйвера: {e}")
            raise
    driver = create_driver("eager", False)
    def set_status(message, court_name):
        pass
    result = parse_court_spb(driver, "spb", "court_name", PersonInitials(surname="Степаненко", name="Иван", patronymic=""), set_status)
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)