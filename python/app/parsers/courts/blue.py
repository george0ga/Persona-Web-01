from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

import time
import torch
print(torch.__file__)

from app.captcha.ocr_model_blue_integration import predict_captcha_from_bytes
from app.parsers.courts.utils import check_502,check_503, make_name_initials
from app.utils.logger import logger

MAX_RETRIES = 15
RETRY_DELAY = 2.5  

def solve_captcha(driver):
    logger.info(f"[solve_captcha] Начата попытка распознания капчи.")
    logger.info(f"[solve_captcha] Поиск элемента с капчей.")
    captcha_img = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'img[src="/captcha.php"]')))
    if not captcha_img:
        logger.warning(f"[solve_captcha] Элемент с капчей не найден, запуск повторной попытки.")
        #driver.refresh()
        input_captcha(driver)
    logger.info(f"[solve_captcha] Элемент с капчей найден.")
    png_data = captcha_img.screenshot_as_png
    logger.info(f"[solve_captcha] Распознавание капчи.")
    captcha_text = predict_captcha_from_bytes(png_data)
    return captcha_text

CAPTCHA_TRY=0 
def input_captcha(driver):
    global CAPTCHA_TRY
    logger.info(f"[input_captcha] Начат процесс ввода капчи.")
    try:
        captcha_text = solve_captcha(driver)
        logger.success(f"[input_captcha] Капча распознана.")
    except Exception as e:
        logger.error(f"[input_captcha] Ошибка при распознавании капчи: {e}")
        return f" Ошибка при распознавании капчи: {e}"
    logger.info(f"[input_captcha] Поиск поля для ввода капчи.")
    
    inputs = driver.find_elements(By.NAME, 'captcha-response')
    if not inputs:
        logger.error(f"[input_captcha] Поле ввода капчи не найдено")
        return " Поле ввода капчи не найдено"
    logger.info(f"[input_captcha] Поле найдено. Попытка отправить капчу.")
    try:
        for c in captcha_text:
            time.sleep(0.05)
            inputs[0].send_keys(c)
        
        buttons = driver.find_elements(By.CLASS_NAME, 'button-normal')
        if not buttons:
            logger.error(f"[input_captcha] Ошибка. Кнопка отправки формы не найдена.")
            return " Кнопка отправки формы не найдена"
        buttons[0].click()
    except Exception as e:
        logger.error(f"[input_captcha] Ошибка при отправке капчи: {e}.")
        raise
    time.sleep(2)
    logger.info(f"[input_captcha] Капча отправлена.")
    
    inputs = driver.find_elements(By.NAME, 'captcha-response')
    captcha_another = driver.find_elements(By.ID, 'kcaptchaForm')
    if not captcha_another:
        logger.success(f"[input_captcha] Капча пройдена.")
        return " Капча пройдена, можно продолжать"
    if not inputs:
        logger.success(f"[input_captcha] Капча пройдена(NO ANOTHER CAPTCHA BY INPUTS).")
        return " Капча пройдена, можно продолжать"
    logger.warning(f"[input_captcha] Капча не пройдена. Запуск повторной проверки.")
    CAPTCHA_TRY+=1
    #driver.refresh()
    time.sleep(2)
    input_captcha(driver)

def extract_table_html(driver):
    logger.info(f"[extract_table_html] Получение таблицы дел.")
    try:
        WebDriverWait(driver,60).until(EC.presence_of_element_located((By.ID,"search_results")))
    except Exception as e:
        logger.error(f"[extract_table_html] Не удалось загрузить таблицу дел.")
    soup = BeautifulSoup(driver.page_source, "html.parser")
    table = soup.find("table", id="tablcont")
    return str(table) if table else "<div class='placeholder'>Нет данных</div>"

def merge_html_tables(html_list):
    logger.info(f"[merge_html_tables] Начато объединение таблиц.")
    if not html_list:
        return "<div class='placeholder'>Нет данных</div>"

    soup = BeautifulSoup(html_list[0], "html.parser")
    base_table = soup.find("table")
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

def extract_total_pages(html):
    logger.info(f"[extract_total_pages] Получения кол-ва страниц.")
    soup = BeautifulSoup(html, 'html.parser')
    pages_block = soup.select_one("ul.paging")
    if not pages_block:
        return 1 

    page_links = pages_block.find_all("a")
    if not page_links:
        return 1

    try:
        last_page_text = page_links[-1].text.strip()
        return int(last_page_text)
    except ValueError:
        logger.error(f"[extract_total_pages] Ошибка получения кол-ва страниц.")
        return 1

def update_page_number(url, new_page_number):
    logger.info(f"[update_page_number] Обновления номера страницы.")
    parts = urlparse(url)
    
    query_params = parse_qsl(parts.query, keep_blank_values=True)
    
    updated_params = []
    found = False
    for key, value in query_params:
        if key == "pageNum_Recordset1":
            updated_params.append((key, str(new_page_number)))
            found = True
        else:
            updated_params.append((key, value))
    
    if not found:
        updated_params.append(("pageNum_Recordset1", str(new_page_number)))
    
    new_query = urlencode(updated_params)
    
    return urlunparse((
        parts.scheme,
        parts.netloc,
        parts.path,
        parts.params,
        new_query,
        parts.fragment
    ))

def check_captcha(driver):
    logger.info(f"[check_captcha] Проверка требования капчи.")
    capthca_page = driver.find_elements(By.ID,"kcaptchaForm")
    if capthca_page:
        logger.warning(f"[check_captcha] Требуется ввести капчу.")
        input_captcha(driver)

def verify_page(driver):
    check_503(driver)
    check_captcha(driver)
    check_503(driver)
    check_captcha(driver) 

def get_all_cases(driver,pages_count):
    logger.info(f"[get_all_cases] Парсинг результата.")
    WebDriverWait(driver, 120).until(
            lambda d: d.find_elements(By.CLASS_NAME, "case-count") or d.find_elements(By.CLASS_NAME, "search-error")
        )
    errors = driver.find_elements(By.CLASS_NAME,"search-error")
    if (errors):
        return "<div class='placeholder'>Дела не найдены</div>"
    all_pages = []
    for page_number in range(pages_count):
        page_url = update_page_number(driver.current_url, page_number)
        driver.get(page_url)
        verify_page(driver)
        try:
            page = extract_table_html(driver)
        except Exception as e:
            logger.error(f"[get_all_cases] Ошибка при получении таблицы категории {e}.")
        all_pages.append(page)
    return merge_html_tables(all_pages)

def parse_category(driver,name_to_check,category):
    logger.info(f"[parse_category] Парсинг категории {category}.")
   
    category_input = driver.find_elements(By.NAME,category)
    search_button = driver.find_elements(By.CLASS_NAME,"search")
    for c in name_to_check:
        category_input[0].send_keys(c)
    search_button[0].click()
    verify_page(driver)
    pages_count = extract_total_pages(driver.page_source)
    return get_all_cases(driver,pages_count)

def parse_court_blue(driver, address,court_name,fullname,set_status):
    court_results = {}
    names = make_name_initials(fullname)
    logger.info(f"[parse_court_blue] Начало проверки.")
    for name_to_check in names:
    #Проверка доступа к сайту
        driver.get(address)
        verify_page(driver)
        
        search_page = driver.find_elements(By.CLASS_NAME,"menu-link")
        if not search_page:
            logger.error("Не найден элемент search_page")
            raise RuntimeError(f"Ошибка при работе с судом: {address}")
        search_page[0].click()
        verify_page(driver)
        WebDriverWait(driver, 10).until(
            lambda d: d.find_elements(By.CLASS_NAME, "bookmarks")
        )
        case_types_buttons = driver.find_elements(By.CLASS_NAME,"bookmarks")

        if not case_types_buttons:
            logger.error("Не найден элемент case_types_buttons")
            raise RuntimeError(f"Ошибка при работе с судом: {address}")
        
        first_button = driver.find_elements(By.ID,"type_0")
        set_status(f"Начало проверки по ФИО : {name_to_check}",court_name)

        #Уголовные, подсудимый 
        logger.info(f"[parse_court_blue] Проверка уголовных дел (подсудимый)")
        set_status(f"Проверка уголовных дел (подсудимый) : {name_to_check}",court_name)
        first_button[0].click()
        time.sleep(0.1)
        verify_page(driver)
        ugolov_defendant_table = parse_category(driver,name_to_check,"U1_DEFENDANT__NAMESS")
        verify_page(driver)

        #Если дела найдены, то нажимается кнопка Новый Поиск
        
        new_search_button = driver.find_elements(By.CLASS_NAME,"new-search")
        if(new_search_button):
            new_search_button[0].click()

        #Очистка после проверки
        logger.info(f"[parse_court_blue] Очистка после провери уголовных дел (подсудимый)")
        clear_button = driver.find_elements(By.CLASS_NAME,"clear")
        clear_button[0].click()
        driver.switch_to.alert.accept()

        #Уголовные, участник 
        logger.info(f"[parse_court_blue] Проверка уголовных дел (участник)")
        #status_manager.update_status(task_id,f"Проверка уголовных дел (участник)",name_to_check)
        set_status(f"Проверка уголовных дел (участник) по ФИО: {name_to_check}",court_name)
        verify_page(driver)
        ugolov_parts_table = parse_category(driver,name_to_check,"U1_PARTS__NAMESS")
        verify_page(driver)
        logger.success(f"[parse_court_blue] Проверка уголовных дел (участник) завершена")

        #Административыне и гражданские 
        logger.info(f"[parse_court_blue] Проверка административыных и гражданских дел")
        set_status(f"Проверка административыных и гражданских дел по ФИО: {name_to_check}",court_name)
        second_button = driver.find_elements(By.ID,"type_1")
        second_button[0].click()
        verify_page(driver)
        adm_and_cit_table = parse_category(driver,name_to_check,"G1_PARTS__NAMESS")
        verify_page(driver)
        logger.success(f"[parse_court_blue] Проверка административыных и гражданских дел завершена")

        #Дела об административных правонарушениях
        logger.info(f"[parse_court_blue] Проверка административыных правонарушений")
        set_status(f"Проверка административыных правонарушений по ФИО: {name_to_check}",court_name)

        third_button = driver.find_elements(By.ID,"type_2")
        third_button[0].click()
        verify_page(driver)
        adm_cases_table = parse_category(driver,name_to_check,"adm_parts__NAMESS")
        verify_page(driver)
        logger.success(f"[parse_court_blue] Проверка административыных правонарушений завершена")

        #Производство по делам
        logger.info(f"[parse_court_blue] Проверка производств по делам")
        set_status(f"Проверка производств по делам по ФИО: {name_to_check}",court_name)

        fourth_button = driver.find_elements(By.ID,"type_3")
        fourth_button[0].click()
        verify_page(driver)
        proizv_table = parse_category(driver,name_to_check,"M_PARTS__NAMESS")
        verify_page(driver)
        logger.success(f"[parse_court_blue] Проверка производств по делам завершена")

        logger.success(f"[parse_court_blue] Подготовка таблица для фронта")
        if court_name not in court_results:
            court_results[court_name] = {}
        court_results[court_name][name_to_check] = {
            "Уголовные дела (Лицо, участвующее в деле)": ugolov_parts_table,
            "Уголовные дела (Подсудимый (осужденный))": ugolov_defendant_table,
            "Административные и гражданские дела": adm_and_cit_table,
            "Дела об административных правонарушениях": adm_cases_table,
            "Производство по делам": proizv_table
        }
        logger.success(f"[parse_court_blue] Таблица готова.")
        set_status(f"Проверка по ФИО {name_to_check} завершена",court_name)
    return court_results


if __name__ == "__main__":
    import json
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from fake_useragent import UserAgent
    from app.schemas.schemas import PersonInitials
    def create_driver(page_load_strategy="normal", headless=False):
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
    result = parse_court_blue(driver, "https://4len.nsk.msudrf.ru/", "court_name", PersonInitials(surname="Акулов", name="Антон", patronymic="Иванович"), set_status)
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)