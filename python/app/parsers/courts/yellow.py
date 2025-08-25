from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from base64 import b64decode
import time
from app.utils.logger import logger
from app.parsers.courts.utils import verify_page
from app.captcha.orc_model_yellow_integration import predict_captcha_from_bytes

MAX_RETRIES = 15
RETRY_DELAY = 5  
FIRST_TIME = True

def solve_captcha(driver):
    logger.info(f"[solve_captcha] Начата попытка распознания капчи.")
    logger.info(f"[solve_captcha] Поиск элемента с капчей.")
    try:
        logger.info(f"[solve_captcha] Поиск элемента input_field")
        input_field = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, "captcha")))
        logger.info(f"[solve_captcha] элемента input_field найден")
    except:
        logger.error(f"[solve_captcha] Не удалось решить капчу.")
        raise
    logger.info(f"[solve_captcha] Поиск доп. элементов")
    parent_td = input_field.find_element(By.XPATH, "./ancestor::td[1]")
    captcha_img = parent_td.find_element(By.TAG_NAME, "img")
    src = captcha_img.get_attribute("src")
    src = src.replace(" ", "")
    if not src.startswith("data:image"):
        raise Exception("Captcha not in base64 fromat: " + src)

    base64_data = src.split(",")[1]
    image_bytes = b64decode(base64_data)
    logger.info(f"[solve_captcha] Попытка решения капчи")
    return predict_captcha_from_bytes(image_bytes)

def extract_table_html(driver):
    logger.info(f"[extract_table_html] Получение таблицы дел.")
    soup = BeautifulSoup(driver.page_source, "html.parser")
    table = soup.find("table", id="tablcont")
    logger.info(f"[extract_table_html] Таблица получена.")
    return str(table) if table else "<div class='placeholder'>Нет данных</div>"

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



def check_captcha(driver):
    logger.info(f"[check_captcha] Проверка сайта на требования к капче.")
    capthca_page = driver.find_elements(By.ID,"captcha")
    if capthca_page:
        logger.info(f"[check_captcha] Сайт требует капчу.")
        return True
    logger.success(f"[check_captcha] Сайт не требует капчу.")
    return False

def check_invalid_captcha_input(driver, name, current_subcategory):
    logger.info(f"[check_invalid_captcha_input] Проверка ошибки после ввода капчи.")

    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.find_elements(By.ID, "error") or d.find_elements(By.TAG_NAME, "h3")
        )
        error_elements = driver.find_elements(By.ID, "error")
        for el in error_elements:
            if "Неверно указан проверочный код с картинки." in el.text.strip():
                logger.error(f"[check_invalid_captcha_input] Капча введена неверно (по #error).")
                return restart_captcha_input(driver, name)

        h3_elements = driver.find_elements(By.TAG_NAME, "h3")
        for el in h3_elements:
            if "Данный запрос некорректен" in el.text:
                logger.error(f"[check_invalid_captcha_input] Капча введена неверно (по <h3>).")
                return restart_captcha_input(driver, name, current_subcategory)

    except Exception as e:
        logger.warning(f"[check_invalid_captcha_input] Ошибка при проверке капчи: {e}")

    logger.success(f"[check_invalid_captcha_input] Капча решена верно.")
    return True


def restart_captcha_input(driver, name, current_subcategory=None):
    try:
        driver.back()
        driver.refresh()
        if current_subcategory:
            select_category_and_subcategory(driver, current_subcategory["category"], current_subcategory["subcategory"])

        logger.info(f"[restart_captcha_input] Ожидание поля ввода капчи.")
        captcha_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "captcha"))
        )
        captcha_input.clear()
        logger.info(f"[restart_captcha_input] Поле найдено. Ввод ФИО.")
        find_and_send_surname_input(driver, name)
        time.sleep(1)
        return False
    except Exception as e:
        logger.error(f"[restart_captcha_input] Ошибка при повторном вводе капчи: {e}")
        return False

def input_captcha_and_press_submit(driver,name,current_subcategory):
    logger.info(f"[input_captcha_and_press_submit] Начинаю отправку капчи.")
    tries = 0
    while tries < MAX_RETRIES:
        logger.info(f"[input_captcha_and_press_submit] Начинаю отправку капчи. Попытка: {tries}")
        find_and_send_captcha(driver)

        logger.info(f"[input_captcha_and_press_submit] Капча отправлена")
        try:
            logger.info(f"[input_captcha_and_press_submit] Поиск кнопки submit")
            submit_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.NAME, "Submit"))
            )
            logger.info(f"[input_captcha_and_press_submit] Конпка найдена, нажимаю...")
            submit_button.click()
            logger.info(f"[input_captcha_and_press_submit] Нажата конпка submit")
        except Exception as e:
            logger.error(f"[input_captcha_and_press_submit] Ошибка при поиске и нажатии кнопки submit")
            return False

        if check_invalid_captcha_input(driver,name,current_subcategory):
            return True 
        tries += 1
    logger.error(f"[input_captcha_and_press_submit] Ошибка ввода капчи — превышено число попыток")
    return False

def select_category_and_subcategory(driver, category_name, subcategory_name):
    logger.info(f"[select_category_and_subcategory] Попытка заново выбрать: {category_name} → {subcategory_name}")
    try:
        find_and_click_change_btn(driver)
        verify_page(driver)

        buttons = get_category_and_subcategory_btns_new(driver)
        if category_name not in buttons:
            logger.warning(f"[select_category_and_subcategory] Категория '{category_name}' не найдена")
            return False

        sub_entry = next(
            (sub for sub in buttons[category_name] if sub["name"] == subcategory_name),
            None
        )
        if not sub_entry:
            logger.warning(f"[select_category_and_subcategory] Подкатегория '{subcategory_name}' не найдена в '{category_name}'")
            return False

        sub_entry["element"].click()
        logger.success(f"[select_category_and_subcategory] Подкатегория '{subcategory_name}' выбрана повторно")
        return True

    except Exception as e:
        logger.exception(f"[select_category_and_subcategory] Ошибка при повторном выборе: {e}")
        return False


def check_and_get_next_page(driver):
    verify_page(driver)
    logger.info(f"[check_and_get_next_page] Проверка наличия кнопки 'Следующая страница")
    try:
        next_page_btn = driver.find_element(By.XPATH, "//a[@title='Следующая страница']")
        next_page_btn.click()
        #WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.ID, "tablcont")))
        logger.info(f"[check_and_get_next_page] Кнопка найдена")
        return extract_table_html(driver)
    except:
        logger.error(f"[check_and_get_next_page] Кнопка 'Следующая страница' не найдена, возвращаю 'end'")
        return "end"

def get_all_cases(driver):
    logger.info(f"[get_all_cases] Ожидаю появления таблицы или ошибки")
    try:
        WebDriverWait(driver, 30).until(
            lambda d: d.find_elements(By.ID, "tablcont") or d.find_elements(By.ID, "error")
        )
        
        if driver.find_elements(By.ID, "error"):
            logger.warning(f"[get_all_cases] Найдена ошибка на странице, возвращаю заглушку")
            return "<div class='placeholder'>Дела не найдены</div>"

        logger.info(f"[get_all_cases] Элемент таблицы найден.")

    except Exception as e:
        logger.error(f"[get_all_cases] Ни таблица, ни ошибка не появились: {e}")
        
    all_pages = []
    logger.info(f"[get_all_cases] Получаю таблицу на первой странице")
    first_page = extract_table_html(driver)
    logger.info(f"[get_all_cases] Таблица получена, добавляю в список таблиц")
    all_pages.append(first_page)
    logger.info(f"[get_all_cases] Первая страница добавлена")

    logger.info(f"[get_all_cases] Начало итерации цикла страниц")
    while True:
        logger.info(f"[get_all_cases] Текущая страница: {len(all_pages) + 1}")
        logger.info(f"[get_all_cases] Проверка наличия и переход к след. странице")
        page = check_and_get_next_page(driver)
        if page == "end":
            logger.info(f"[get_all_cases] Достигнута последняя страница, выхожу из цикла")
            break
        logger.info(f"[get_all_cases] Добавление страницы в список.")
        all_pages.append(page)
        logger.info(f"[get_all_cases] Добавлена новая страница, всего страниц: {len(all_pages)}")

    logger.success(f"[get_all_cases] Все страницы собраны, объединяю таблицы")
    return merge_html_tables(all_pages)

def find_and_click_change_btn(driver):
    logger.info(f"[find_and_click_change_btn] Поиск и клик по кнопке 'Изменить'")
    try:
        logger.info(f"[find_and_click_change_btn] Ожидание появления элмента")
        change_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//a[text()='Изменить']"))
        )
        logger.info(f"[find_and_click_change_btn] Элемент появился, нажимаю...")
        change_button.click()
        logger.success(f"[find_and_click_change_btn] Элемент нажат")
    except Exception as e:
        logger.error(f"[find_and_click_change_btn] Ошибка при поиске и нажатии кнопки 'Изменить'")

def find_and_send_surname_input(driver,name):
    logger.info(f"[find_and_send_surname_input] Начало попытки ввода фамилии: {name}")
    time.sleep(1)
    global FIRST_TIME
    try:
        if FIRST_TIME:
            logger.info(f"[find_and_send_surname_input] Первая загрузка — проверка поля 'U1_DEFENDANT__NAMESS'")
            try:
                WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.NAME, "U1_DEFENDANT__NAMESS"))
                )
                logger.info(f"[find_and_send_surname_input] Поле 'U1_DEFENDANT__NAMESS' найдено")
                FIRST_TIME = False
            except TimeoutException:
                logger.error(f"[find_and_send_surname_input] Поле 'U1_DEFENDANT__NAMESS' не найдено за 30 секунд")
                raise

        logger.info(f"[find_and_send_surname_input] Поиск поля ввода фамилии по XPATH")
        try:
            surname_input = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//td[text()='Фамилия']/following-sibling::td/input")
                )
            )
            logger.info(f"[find_and_send_surname_input] Поле для ввода фамилии найдено — вводим: {name}")
            for c in name:
                surname_input.send_keys(c)
            logger.success(f"[find_and_send_surname_input] Ввод фамилии '{name}' успешно завершён")
        except TimeoutException:
            logger.error(f"[find_and_send_surname_input] Поле для ввода фамилии не найдено за 30 секунд")
            raise

    except Exception as e:
        logger.exception(f"[find_and_send_surname_input] Ошибка при вводе фамилии: {e}")

def find_and_click_back_btn(driver):
    logger.info(f"[find_and_click_back_btn] Попытка найти и нажать кнопку 'Поиск информации по делам'")
    try:
        logger.info(f"[find_and_click_back_btn] Ожидание доступности кнопки...")
        back_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//a[b[contains(text(),'Поиск информации по делам')]]"))
        )
        logger.info(f"[find_and_click_back_btn] Кнопка найдена. Выполняется клик...")
        back_button.click()
        logger.success(f"[find_and_click_back_btn] Кнопка 'Поиск информации по делам' успешно нажата")

    except (TimeoutException, NoSuchElementException) as e:
        #html_snippet = driver.page_source[:1000]
        #logger.error(f"[find_and_click_back_btn] Кнопка не найдена. Фрагмент страницы:\n{html_snippet}")
        logger.error(f"[find_and_click_back_btn] Кнопка не найдена.")
        logger.exception(f"[find_and_click_back_btn] Исключение: {e}")
        raise RuntimeError("[find_and_click_back_btn] Кнопка 'Поиск информации по делам' не найдена")

def find_and_send_captcha(driver):
    logger.info(f"[find_and_send_captcha] Запуск решения и ввода капчи")

    try:
        logger.info(f"[find_and_send_captcha] Попытка распознать капчу")
        capcha_text = solve_captcha(driver)
        logger.success(f"[find_and_send_captcha] Капча распознана: {capcha_text}")
    except Exception as e:
        logger.error(f"[find_and_send_captcha] Ошибка при распознавании капчи: {e}")
        raise

    try:
        logger.info(f"[find_and_send_captcha] Ожидание поля для ввода капчи")
        capcha_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "captcha"))
        )
        logger.info(f"[find_and_send_captcha] Поле найдено. Вводим капчу...")
    except TimeoutException:
        logger.error(f"[find_and_send_captcha] Поле для капчи не найдено за 30 секунд")
        raise

    try:
        for c in capcha_text:
            capcha_input.send_keys(c)
        logger.success(f"[find_and_send_captcha] Капча успешно введена")
    except Exception as e:
        logger.warning(f"[find_and_send_captcha] Ошибка при первом вводе капчи: {e}")
        try:
            capcha_input = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.NAME, "captcha"))
            )
            for c in capcha_text:
                capcha_input.send_keys(c)
            logger.success(f"[find_and_send_captcha] Повторный ввод капчи успешен")
        except Exception as e2:
            logger.error(f"[find_and_send_captcha] Повторный ввод капчи не удался: {e2}")
            raise

def get_category_and_subcategory_btns(driver):
    logger.info(f"[get_category_and_subcategory_btns] Начало парсинга категорий")

    try:
        logger.info(f"[get_category_and_subcategory_btns] Ожидание загрузки строк таблицы и подкатегорий")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table > tbody > tr"))
        )
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[onclick*='select_delo_id_new']"))
        )
    except TimeoutException:
        logger.error(f"[get_category_and_subcategory_btns] Категории не загрузились — таймаут")
        return {}

    rows = driver.find_elements(By.CSS_SELECTOR, "table > tbody > tr")
    results = {}
    current_category = None

    for idx, row in enumerate(rows):
        try:
            logger.debug(f"[get_category_and_subcategory_btns] Обработка строки {idx + 1}")
            strongs = row.find_elements(By.CSS_SELECTOR, "strong")
            if strongs:
                current_category = strongs[0].text.strip()
                if current_category.lower() == "отмена":
                    logger.debug(f"[get_category_and_subcategory_btns] Категория 'отмена' пропущена")
                    current_category = None
                    continue
                results[current_category] = []
                logger.debug(f"[get_category_and_subcategory_btns] Найдена категория: {current_category}")
                continue

            divs = row.find_elements(By.CSS_SELECTOR, "div[onclick*='select_delo_id_new']")
            if divs:
                sub_name = divs[0].text.strip()
                if sub_name.lower() == "отмена":
                    logger.debug(f"[get_category_and_subcategory_btns] Подкатегория 'отмена' пропущена")
                    continue
                if current_category:
                    results[current_category].append({
                        "name": sub_name,
                        "element": divs[0]
                    })
                    logger.debug(f"[get_category_and_subcategory_btns] Добавлена подкатегория '{sub_name}' в '{current_category}'")

        except Exception as e:
            logger.warning(f"[get_category_and_subcategory_btns] Ошибка при обработке строки {idx + 1}: {e}")

    if not results:
        logger.warning(f"[get_category_and_subcategory_btns] Категории не найдены (results пустой)")
    else:
        logger.success(f"[get_category_and_subcategory_btns] Парсинг завершён. Найдено категорий: {len(results)}")

    return results

def get_category_and_subcategory_btns_new(driver):
    logger.info("[get_category_and_subcategory_buttons] Парсинг категорий и подкатегорий")

    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "content"))
        )
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table > tbody > tr"))
        )
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[onclick*='select_delo_id_new']"))
        )
    except:
        logger.error("[get_category_and_subcategory_buttons] Элемент #content не найден")
    try:
        container = driver.find_element(By.ID, "content")
    except Exception as e:
        logger.error("[get_category_and_subcategory_buttons] Элемент #content не найден")
        return {}

    result = {}
    current_category = None

    divs = container.find_elements(By.XPATH, ".//div")

    for div in divs:
        try:
            # Категория — если div содержит <strong>
            strongs = div.find_elements(By.TAG_NAME, "strong")
            if strongs:
                current_category = strongs[0].text.strip()
                if(current_category != "Отмена"):
                    result[current_category] = []
                    logger.debug(f"[get_category_and_subcategory_buttons] Найдена категория: {current_category}")
                continue

            # Подкатегория — отступ + onclick
            style = div.get_attribute("style") or ""
            onclick = div.get_attribute("onclick")
            if "padding-left: 30px" in style and onclick:
                sub_name = div.text.strip()
                if current_category:
                    result[current_category].append({
                        "name": sub_name,
                        "element": div
                    })
                    logger.debug(f"[get_category_and_subcategory_buttons] Подкатегория '{sub_name}' добавлена в '{current_category}'")

        except Exception as e:
            logger.warning(f"[get_category_and_subcategory_buttons] Ошибка при обработке div: {e}")

    logger.success(f"[get_category_and_subcategory_buttons] Готово. Категорий: {len(result)}")
    return result

def find_and_click_search_btn(driver):
    logger.info(f"[find_and_click_search_btn] Попытка найти и нажать кнопку 'Поиск информации по делам'")

    try:
        logger.info(f"[find_and_click_search_btn] Ожидание доступности кнопки...")
        search_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[b[contains(text(),'Поиск информации по делам')]]")
            )
        )
    except TimeoutException:
        logger.error(f"[find_and_click_search_btn] Кнопка не найдена за 30 секунд")
        return { "ошибка: Не найдена кнопка 'Поиск информации по делам'" : "" }

    try:
        logger.info(f"[find_and_click_search_btn] Кнопка найдена. Выполняется клик...")
        search_button.click()
        logger.success(f"[find_and_click_search_btn] Кнопка 'Поиск информации по делам' успешно нажата")
    except Exception as e:
        logger.exception(f"[find_and_click_search_btn] Ошибка при нажатии кнопки: {e}")
        return { "ошибка: Не удалось нажать кнопку 'Поиск информации по делам'" : "" }

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
        else:
            if fullname.name:
                # Иванов И.
                initials = f"{fullname.surname} {fullname.name[0]}. "
                names.append(initials)
                logger.debug(f"[make_name_initials] Добавлен вариант с первой буквой имени: {initials}")

                # Иванов Иван
                full = f"{fullname.surname} {fullname.name}"
                names.append(full)
                logger.debug(f"[make_name_initials] Добавлен вариант с именем без отчества: {full}")

            # Иванов
            names.append(fullname.surname)
            logger.debug(f"[make_name_initials] Добавлена только фамилия: {fullname.surname}")

        logger.success(f"[make_name_initials] Всего сформировано вариантов: {len(names)}")
        return names

    except Exception as e:
        logger.exception(f"[make_name_initials] Ошибка при формировании ФИО: {e}")
        return [fullname.surname]

def get_court_type(driver, address):
    logger.info(f"[get_court_type] Определение типа суда по адресу: {address}")

    try:
        driver.get(address)
        logger.info(f"[get_court_type] Страница загружена")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.menu__link"))
        )
        all_links = driver.find_elements(By.CSS_SELECTOR, "a.menu__link")
        sud_delo_button = None

        for link in all_links:
            href = link.get_attribute("href")
            if "sud_delo" in href:
                sud_delo_button = link
                break

        if sud_delo_button is None:
            logger.error(f"[get_court_type] Не найдена кнопка 'Судебное делопроизводство' на сайте {address}")
            return {f"Сайт {address}": {"__error__": "Ошибка при работе с судом. Не найдено кнопка судебное делопроизовдство"}}

        logger.info(f"[get_court_type] Кнопка 'Судебное делопроизводство' найдена — выполняется переход")
        driver.execute_script("arguments[0].scrollIntoView(true);", sud_delo_button)
        time.sleep(0.3)
        sud_delo_button.click()
        logger.info(f"[get_court_type] Переход выполнен.")
        logger.info(f"[get_court_type] Попытка загрузить элементы.")
        is_multiserver = driver.find_elements(By.CLASS_NAME, "statUl")
        is_modern = driver.find_elements(By.CLASS_NAME, "round-border-container")
        is_unavailable = driver.find_elements(By.CLASS_NAME, "error_errorer")
        if is_multiserver:
            logger.success(f"[get_court_type] Тип суда: multi")
            return "multi"
        if is_modern:
            logger.success(f"[get_court_type] Тип суда: modern")
            return "modern"
        if is_unavailable:
            logger.warning(f"[get_court_type] Сайт недоступен: ошибка-доступа")
            return "unavailable"

        logger.success(f"[get_court_type] Тип суда: regular")
        return "regular"

    except Exception as e:
        logger.exception(f"[get_court_type] Ошибка при определении типа суда: {e}")
        return {f"Сайт {address}": {"__error__": "Ошибка при работе с судом."}}

def regular_type_court_check(driver, address,court_name, names):
    logger.info(f"[regular_type_court_check] Запуск проверки обычного типа суда по адресу: {address}")
    court_results = {}

    try:
        for name_to_check in names:
            logger.info(f"[regular_type_court_check] Проверка для имени: {name_to_check}")
            driver.get(address)
            verify_page(driver)

            logger.info(f"[regular_type_court_check] Поиск кнопки 'Судебное делопроизводство'")
            all_links = driver.find_elements(By.CSS_SELECTOR, "a.menu__link")
            sud_delo_button = next((link for link in all_links if "sud_delo" in link.get_attribute("href")), None)

            if sud_delo_button is None:
                logger.error(f"[regular_type_court_check] Кнопка 'Судебное делопроизводство' не найдена")
                return {f"Сайт {address}": {"__error__": "Ошибка при работе с судом. Не найдена кнопка судебное делопроизводство"}}

            court_results.setdefault(court_name, {})[name_to_check] = {}

            sud_delo_button.click()
            verify_page(driver)

            find_and_click_search_btn(driver)
            verify_page(driver)

            is_captcha_required = check_captcha(driver)

            find_and_click_change_btn(driver)
            verify_page(driver)
            visited_categories = set()
            category_buttons = get_category_and_subcategory_btns_new(driver)
            logger.info(f"[regular_type_court_check] Категорий для обработки: {len(category_buttons)}")
            logger.info("=== Начало итерации по категориям ===")

            for category_name, subcategories in category_buttons.items():
                if category_name in visited_categories:
                    logger.debug(f"[regular_type_court_check] Категория '{category_name}' уже была обработана — пропускаем")
                    continue

                logger.info(f"[regular_type_court_check] Обработка категории: {category_name}")

                for subcategory in subcategories:
                    logger.info(f"[regular_type_court_check] Попытка нажать подкатегорию: {subcategory['name']}")
                    current_subcategory = {
                        "category": category_name,
                        "subcategory": subcategory["name"]
                    }
                    fresh_category_buttons = get_category_and_subcategory_btns_new(driver)
                    refreshed_element = next(
                        (sub["element"] for sub in fresh_category_buttons.get(category_name, [])
                        if sub["name"] == subcategory["name"]), None)

                    if refreshed_element is None:
                        logger.warning(f"[regular_type_court_check] Не удалось найти элемент подкатегории '{subcategory['name']}'")
                        continue

                    refreshed_element.click()
                    logger.info(f"[regular_type_court_check] Подкатегория '{subcategory['name']}' нажата")

                    verify_page(driver)
                    try:
                        WebDriverWait(driver, 40).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "#content .box.box_common.m-all_m"))
                        )
                        logger.debug(f"[regular_type_court_check] Вторая форма загружена")
                    except TimeoutException:
                        logger.warning(f"[regular_type_court_check] Вторая форма не загрузилась — подкатегория пропущена")
                        continue

                    try:
                        case_type_div = WebDriverWait(driver, 30).until(
                            EC.presence_of_element_located((By.ID, "case_type"))
                        )
                        category_text = case_type_div.find_element(By.TAG_NAME, "div").text.strip()
                        logger.debug(f"[regular_type_court_check] Тип дел: {category_text}")
                    except Exception as e:
                        logger.warning(f"[regular_type_court_check] Не удалось извлечь тип дел: {e}")
                        continue

                    find_and_send_surname_input(driver, name_to_check)
                    logger.info(f"[regular_type_court_check] Введена фамилия: {name_to_check}")
                    verify_page(driver)

                    if is_captcha_required:
                        if input_captcha_and_press_submit(driver, name_to_check,current_subcategory):
                            logger.info(f"[regular_type_court_check] Капча пройдена успешно")
                        else:
                            logger.warning(f"[regular_type_court_check] Не удалось решить капчу")
                            continue
                    else:
                        try:
                            submit_button = driver.find_element(By.NAME, "Submit")
                            submit_button.click()
                            logger.info(f"[regular_type_court_check] Нажата кнопка 'Submit'")
                        except Exception as e:
                            logger.warning(f"[regular_type_court_check] Ошибка при нажатии 'Submit': {e}")
                            continue

                    html_table = get_all_cases(driver)
                    logger.info(f"[regular_type_court_check] Таблица дел получена ({len(html_table)} символов)")

                    court_results[court_name][name_to_check].setdefault(category_name, {})[subcategory["name"]] = html_table
                    logger.success(f"[regular_type_court_check] Результат добавлен: {court_name} > {name_to_check} > {category_name} > {subcategory['name']}")

                    find_and_click_back_btn(driver)
                    logger.info(f"[regular_type_court_check] Выполнен возврат назад")
                    verify_page(driver)
                    find_and_click_change_btn(driver)
                    logger.info(f"[regular_type_court_check] Нажата кнопка 'Изменить'")
                # Добавляем в список посещённых категорий
                visited_categories.add(category_name)
            logger.info("=== Конец итерации по имени ===")
    except Exception as e:
        logger.exception(f"[regular_type_court_check] Ошибка при проверке: {e}")
        raise

    return court_results

def moder_find_and_send_surname_input(driver, name):
    logger.info(f"[moder_find_and_send_surname_input] Попытка ввода фамилии (modern): {name}")
    time.sleep(1)

    try:
        logger.info(f"[moder_find_and_send_surname_input] Поиск поля по ID: 'parts__namess'")
        surname_input = driver.find_element(By.ID, "parts__namess")
        logger.info(f"[moder_find_and_send_surname_input] Поле найдено. Начинаем посимвольный ввод")

        for c in name:
            surname_input.send_keys(c)

        logger.success(f"[moder_find_and_send_surname_input] Ввод имени '{name}' завершён")

    except Exception as e:
        logger.exception(f"[moder_find_and_send_surname_input] Ошибка при вводе имени '{name}': {e}")
        raise

def modern_solve_captcha(driver):
    logger.info(f"[modern_solve_captcha] Начало распознавания капчи (modern)")

    try:
        logger.info(f"[modern_solve_captcha] Ожидание поля ввода капчи")
        input_field = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "captcha"))
        )
    except TimeoutException:
        logger.error(f"[modern_solve_captcha] Поле капчи не найдено за 30 секунд")
        raise

    try:
        logger.info(f"[modern_solve_captcha] Поиск изображения капчи рядом с полем")
        captcha_img = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='captcha']/following::img[1]"))
        )
        src = captcha_img.get_attribute("src").replace(" ", "")

        if not src.startswith("data:image"):
            logger.error(f"[modern_solve_captcha] Капча не в base64-формате: {src[:30]}...")
            raise ValueError("Captcha not in base64 format")

        base64_data = src.split(",")[1]
        image_bytes = b64decode(base64_data)

        logger.info(f"[modern_solve_captcha] Капча успешно декодирована. Отправка на распознавание...")
        captcha_text = predict_captcha_from_bytes(image_bytes)
        logger.success(f"[modern_solve_captcha] Капча распознана: {captcha_text}")
        return captcha_text

    except Exception as e:
        logger.exception(f"[modern_solve_captcha] Ошибка при распознавании капчи: {e}")
        raise

def modern_find_and_send_captcha(driver):
    logger.info(f"[modern_find_and_send_captcha] Запуск процедуры распознавания и ввода капчи")

    try:
        captcha_text = modern_solve_captcha(driver)
        logger.info(f"[modern_find_and_send_captcha] Капча распознана: {captcha_text}")
    except Exception as e:
        logger.exception(f"[modern_find_and_send_captcha] Ошибка при распознавании капчи: {e}")
        raise

    try:
        logger.info(f"[modern_find_and_send_captcha] Поиск поля для ввода капчи")
        capcha_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "captcha"))
        )
    except TimeoutException:
        logger.error(f"[modern_find_and_send_captcha] Поле для капчи не найдено за 30 секунд")
        raise

    try:
        logger.info(f"[modern_find_and_send_captcha] Вводим капчу посимвольно (основная попытка)")
        for c in captcha_text:
            capcha_input.send_keys(c)
        logger.success(f"[modern_find_and_send_captcha] Ввод капчи завершён успешно")

    except Exception as e:
        logger.warning(f"[modern_find_and_send_captcha] Ошибка при вводе капчи: {e}")
        try:
            logger.info(f"[modern_find_and_send_captcha] Повторная попытка ввода капчи")
            capcha_input = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.NAME, "captcha"))
            )
            for c in captcha_text:
                capcha_input.send_keys(c)
            logger.success(f"[modern_find_and_send_captcha] Повторный ввод капчи выполнен успешно")
        except Exception as e2:
            logger.exception(f"[modern_find_and_send_captcha] Повторный ввод капчи не удался: {e2}")
            raise

def modern_check_invalid_captcha_input(driver, name):
    logger.info(f"[modern_check_invalid_captcha_input] Проверка результата ввода капчи")

    try:
        # Проверка блока с ошибкой
        error = driver.find_elements(By.ID, "error")
        if error:
            logger.warning(f"[modern_check_invalid_captcha_input] Обнаружена ошибка: неверная капча (ID='error')")
            driver.back()
            driver.refresh()

            logger.info(f"[modern_check_invalid_captcha_input] Повторный ввод капчи после ошибки")
            capcha_input = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.NAME, "captcha"))
            )
            moder_find_and_send_surname_input(driver, name)
            capcha_input.clear()
            time.sleep(1)
            return False

        # Проверка по тексту h3
        h3 = driver.find_element(By.TAG_NAME, "h3")
        if "Данный запрос некорректен" in h3.text:
            logger.warning(f"[modern_check_invalid_captcha_input] Ошибка: некорректный запрос (captcha invalid)")
            driver.back()
            driver.refresh()

            logger.info(f"[modern_check_invalid_captcha_input] Повторный ввод капчи после ошибки h3")
            capcha_input = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.NAME, "captcha"))
            )
            moder_find_and_send_surname_input(driver, name)
            capcha_input.clear()
            time.sleep(1)
            return False

    except Exception as e:
        logger.exception(f"[modern_check_invalid_captcha_input] Ошибка при проверке валидности капчи: {e}")

    logger.info(f"[modern_check_invalid_captcha_input] Ошибок не обнаружено — капча прошла успешно")
    return True

def modern_input_captcha_and_press_submit(driver, name):
    logger.info(f"[modern_input_captcha_and_press_submit] Начало попыток ввода капчи (максимум {MAX_RETRIES})")
    tries = 0

    while tries < MAX_RETRIES:
        logger.info(f"[modern_input_captcha_and_press_submit] Попытка {tries + 1}/{MAX_RETRIES}")

        try:
            modern_find_and_send_captcha(driver)
            logger.info(f"[modern_input_captcha_and_press_submit] Капча введена")
        except Exception as e:
            logger.warning(f"[modern_input_captcha_and_press_submit] Ошибка при вводе капчи: {e}")
            tries += 1
            continue

        try:
            submit_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.ID, "searchBtn"))
            )
            submit_button.click()
            logger.info(f"[modern_input_captcha_and_press_submit] Нажата кнопка 'searchBtn'")
        except Exception as e:
            logger.warning(f"[modern_input_captcha_and_press_submit] Не удалось нажать 'searchBtn': {e}")
            return False

        try:
            if modern_check_invalid_captcha_input(driver, name):
                logger.success(f"[modern_input_captcha_and_press_submit] Капча принята с попытки {tries + 1}")
                return True
            else:
                logger.warning(f"[modern_input_captcha_and_press_submit] Капча не прошла проверку — пробуем заново")
        except Exception as e:
            logger.exception(f"[modern_input_captcha_and_press_submit] Ошибка при проверке валидности капчи: {e}")
            return False

        tries += 1

    logger.error(f"[modern_input_captcha_and_press_submit] Превышено количество попыток ({MAX_RETRIES}) — капча не пройдена")
    return False

def modern_extract_table_html(driver):
    logger.info(f"[modern_extract_table_html] Попытка извлечь таблицу с результатами")

    try:
        logger.info(f"[modern_extract_table_html] Ожидание появления элемента с ID 'resultTable'")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "resultTable"))
        )
    except TimeoutException:
        logger.warning(f"[modern_extract_table_html] Таблица не найдена за 10 секунд")
        return "<div class='placeholder'>Таблица не найдена</div>"

    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        table = soup.find("table", class_="law-case-table")

        if table:
            logger.success(f"[modern_extract_table_html] Таблица успешно найдена и извлечена")
            return str(table)
        else:
            logger.warning(f"[modern_extract_table_html] Таблица отсутствует в разметке — возвращается заглушка")
            return "<div class='placeholder'>Нет данных</div>"

    except Exception as e:
        logger.exception(f"[modern_extract_table_html] Ошибка при извлечении таблицы: {e}")
        return "<div class='placeholder'>Ошибка при получении таблицы</div>"

def modern_check_and_get_next_page(driver):
    logger.info(f"[modern_check_and_get_next_page] Проверка наличия кнопки 'Следующая страница'")

    try:
        verify_page(driver)
    except Exception as e:
        logger.warning(f"[modern_check_and_get_next_page] Ошибка при проверке страницы перед переходом: {e}")

    try:
        logger.info(f"[modern_check_and_get_next_page] Ожидание кликабельности кнопки '»'")
        next_page_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "»"))
        )
        next_page_btn.click()
        logger.info(f"[modern_check_and_get_next_page] Кнопка 'Следующая страница' нажата")

        return modern_extract_table_html(driver)

    except TimeoutException:
        logger.warning(f"[modern_check_and_get_next_page] Кнопка 'Следующая страница' не найдена за 10 секунд — конец страниц")
        return "end"

    except Exception as e:
        logger.exception(f"[modern_check_and_get_next_page] Ошибка при переходе на следующую страницу: {e}")
        return "end"

def modern_get_all_cases(driver):
    logger.info(f"[modern_get_all_cases] Запуск парсинга результатов (modern)")

    logger.info(f"[modern_get_all_cases] Ожидание текста 'не найдено' или появления таблицы")
    try:
        WebDriverWait(driver, 30).until(
            lambda d: 
                d.find_elements(By.CLASS_NAME, "name-instanse") or
                d.find_elements(By.ID, "resultTable")
        )

        result_blocks = driver.find_elements(By.CLASS_NAME, "name-instanse")
        for block in result_blocks:
            if "Данных по запросу не найдено" in block.text:
                logger.warning(f"[modern_get_all_cases] На странице указано: 'Данных по запросу не найдено'")
                return "<div class='placeholder'>Дела не найдены</div>"

        logger.info(f"[modern_get_all_cases] Таблица resultTable найдена")

    except TimeoutException:
        logger.warning(f"[modern_get_all_cases] Ни таблица, ни блок с ошибкой не появились за 30 секунд")
        return "<div class='placeholder'>Результаты не найдены</div>"

    all_pages = []

    try:
        first_page = modern_extract_table_html(driver)
        all_pages.append(first_page)
        logger.info(f"[modern_get_all_cases] Первая страница сохранена (длина: {len(first_page)} символов)")
    except Exception as e:
        logger.exception(f"[modern_get_all_cases] Ошибка при извлечении первой страницы: {e}")
        return "<div class='placeholder'>Ошибка при парсинге первой страницы</div>"

    while True:
        logger.info(f"[modern_get_all_cases] Начало итерации цикла страниц")
        try:
            page = modern_check_and_get_next_page(driver)
            if isinstance(page, str):
                logger.info(f"[modern_get_all_cases] Результат CheckAndGetNextPage: {page[:100]}...")
        except Exception as e:
            logger.exception(f"[modern_get_all_cases] Ошибка при переходе к следующей странице: {e}")
            break

        if page == "end":
            logger.info(f"[modern_get_all_cases] Достигнут конец страниц — завершение цикла")
            break

        all_pages.append(page)
        logger.info(f"[modern_get_all_cases] Добавлена новая страница. Всего страниц: {len(all_pages)}")

    logger.success(f"[modern_get_all_cases] Все страницы собраны. Объединение таблиц")
    return merge_html_tables(all_pages)

def modern_find_and_click_search_btn(driver):
    logger.info(f"[modern_find_and_click_search_btn] Поиск и клик по кнопке 'Поиск информации по делам' (modern)")

    try:
        logger.info(f"[modern_find_and_click_search_btn] Ожидание кнопки с ID 'show-sf'")
        search_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "show-sf"))
        )
    except TimeoutException:
        logger.error(f"[modern_find_and_click_search_btn] Кнопка не найдена за 30 секунд")
        return { "ошибка: Не найдена кнопка 'Поиск информации по делам'" : "" }

    try:
        logger.info(f"[modern_find_and_click_search_btn] Кнопка найдена. Выполняется клик...")
        search_button.click()
        logger.success(f"[modern_find_and_click_search_btn] Кнопка 'Поиск информации по делам' успешно нажата")
    except Exception as e:
        logger.exception(f"[modern_find_and_click_search_btn] Ошибка при нажатии кнопки: {e}")
        return { "ошибка: Не удалось нажать кнопку 'Поиск информации по делам'" : "" }
    
def modern_type_court_check(driver, address,court_name, names):
    logger.info(f"[modern_type_court_check] Запуск проверки modern-суда по адресу: {address}")
    court_results = {}

    try:
        for name_to_check in names:
            logger.info(f"[modern_type_court_check] Проверка для ФИО: {name_to_check}")
            driver.get(address)
            verify_page(driver)

            all_links = driver.find_elements(By.CSS_SELECTOR, "a.menu__link")
            sud_delo_button = next((link for link in all_links if "sud_delo" in link.get_attribute("href")), None)

            if sud_delo_button is None:
                logger.error(f"[modern_type_court_check] Не найдена кнопка 'Судебное делопроизводство'")
                return {f"Сайт {address}": {"__error__": "Ошибка при работе с судом. Не найдена кнопка судебное делопроизводство"}}

            court_results.setdefault(court_name, {})[name_to_check] = {}

            sud_delo_button.click()
            verify_page(driver)

            modern_find_and_click_search_btn(driver)
            verify_page(driver)

            is_captcha_required = check_captcha(driver)
            verify_page(driver)

            logger.info(f"[modern_type_court_check] === Начало итерации по категориям ===")
            category_index = 0

            while True:
                try:
                    category_select_elem = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "process-type"))
                    )
                    categories = category_select_elem.find_elements(By.TAG_NAME, "optgroup")

                    if category_index >= len(categories):
                        break

                    category = categories[category_index]
                    category_name = category.get_attribute("label")
                    logger.info(f"[modern_type_court_check] Обработка категории: {category_name}")

                    subcategories = [
                        {"name": s.text.strip(), "value": s.get_attribute("value")}
                        for s in category.find_elements(By.TAG_NAME, "option")
                    ]

                    for sub in subcategories:
                        subcategory_name = sub["name"]
                        logger.info(f"[modern_type_court_check] Подкатегория: {subcategory_name}")

                        # Обновляем select и подкатегорию
                        category_select_elem = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, "process-type"))
                        )
                        categories = category_select_elem.find_elements(By.TAG_NAME, "optgroup")
                        current_category = categories[category_index]

                        fresh_sub = next(
                            (s for s in current_category.find_elements(By.TAG_NAME, "option") if s.text.strip() == subcategory_name),
                            None
                        )

                        if not fresh_sub:
                            logger.warning(f"[modern_type_court_check] Не найдена подкатегория: {subcategory_name}")
                            continue

                        fresh_sub.click()
                        verify_page(driver)

                        moder_find_and_send_surname_input(driver, name_to_check)
                        logger.info(f"[modern_type_court_check] Введена фамилия: {name_to_check}")
                        verify_page(driver)

                        if is_captcha_required:
                            if not modern_input_captcha_and_press_submit(driver, name_to_check):
                                logger.warning(f"[modern_type_court_check] Не удалось пройти капчу")
                                continue
                        else:
                            try:
                                submit_button = WebDriverWait(driver, 10).until(
                                    EC.element_to_be_clickable((By.NAME, "Submit"))
                                )
                                submit_button.click()
                                logger.info(f"[modern_type_court_check] Нажата кнопка 'Submit'")
                            except Exception as e:
                                logger.warning(f"[modern_type_court_check] Ошибка при нажатии 'Submit': {e}")
                                continue

                        html_table = modern_get_all_cases(driver)
                        logger.info(f"[modern_type_court_check] Таблица дел получена (длина: {len(html_table)} символов)")

                        court_results[court_name][name_to_check].setdefault(category_name, {})[subcategory_name] = html_table
                        logger.success(f"[modern_type_court_check] Результат сохранён для подкатегории '{subcategory_name}'")

                        modern_find_and_click_search_btn(driver)
                        verify_page(driver)

                    category_index += 1

                except Exception as e:
                    logger.exception(f"[modern_type_court_check] Ошибка при обработке категории {category_index}: {e}")
                    break

            logger.info(f"[modern_type_court_check] === Конец итерации по имени: {name_to_check} ===")

    except Exception as e:
        logger.exception(f"[modern_type_court_check] Критическая ошибка при обработке сайта {address}: {e}")

    return court_results

def multiserver_type_court_check(driver, address, court_name, names):
    logger.info(f"[multiserver_type_court_check] Запуск проверки multiserver-суда по адресу: {address}")
    court_results = {}

    try:
        for name_to_check in names:
            logger.info(f"[multiserver_type_court_check] Проверка для ФИО: {name_to_check}")
            driver.get(address)
            verify_page(driver)

            all_links = driver.find_elements(By.CSS_SELECTOR, "a.menu__link")
            sud_delo_button = next((link for link in all_links if "sud_delo" in link.get_attribute("href")), None)

            if sud_delo_button is None:
                logger.error(f"[multiserver_type_court_check] Кнопка 'Судебное делопроизводство' не найдена")
                return {f"Сайт {address}": {"__error__": "Ошибка при работе с судом. Не найдена кнопка судебное делопроизводство"}}

            ul = driver.find_element(By.CLASS_NAME, "statUl")
            li_elements = ul.find_elements(By.TAG_NAME, "li")

            for li in li_elements:
                server_link = li.find_element(By.TAG_NAME, "a")
                server_link.click()

                court_results.setdefault(court_name, {})[name_to_check] = {}

                sud_delo_button.click()
                verify_page(driver)
                find_and_click_search_btn(driver)
                verify_page(driver)

                is_captcha_required = check_captcha(driver)
                verify_page(driver)

                category_buttons = get_category_and_subcategory_btns_new(driver)
                logger.info(f"[multiserver_type_court_check] Категорий найдено: {len(category_buttons)}")
                logger.info("=== Начало итерации по категориям ===")

                for category_name, subcategories in category_buttons.items():
                    logger.info(f"[multiserver_type_court_check] Категория: {category_name}")

                    for subcategory in subcategories:
                        logger.info(f"[multiserver_type_court_check] Подкатегория: {subcategory['name']}")

                        fresh_category_buttons = get_category_and_subcategory_btns_new(driver)

                        refreshed_element = next(
                            (sub["element"] for sub in fresh_category_buttons.get(category_name, [])
                             if sub["name"] == subcategory["name"]), None)

                        if not refreshed_element:
                            logger.warning(f"[multiserver_type_court_check] Не найдена подкатегория: {subcategory['name']}")
                            continue

                        refreshed_element.click()
                        logger.info(f"[multiserver_type_court_check] Клик по подкатегории '{subcategory['name']}' выполнен")

                        verify_page(driver)
                        try:
                            WebDriverWait(driver, 50).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "#content .box.box_common.m-all_m"))
                            )
                            logger.debug("[multiserver_type_court_check] Вторая форма загружена")
                        except TimeoutException:
                            logger.warning("[multiserver_type_court_check] Вторая форма не загрузилась — подкатегория пропущена")
                            continue

                        try:
                            case_type_div = WebDriverWait(driver, 30).until(
                                EC.presence_of_element_located((By.ID, "case_type"))
                            )
                            category_text = case_type_div.find_element(By.TAG_NAME, "div").text.strip()
                            logger.debug(f"[multiserver_type_court_check] Тип дела: {category_text}")
                        except Exception as e:
                            logger.warning(f"[multiserver_type_court_check] Ошибка получения типа дела: {e}")
                            continue

                        find_and_send_surname_input(driver, name_to_check)
                        logger.info(f"[multiserver_type_court_check] Введена фамилия: {name_to_check}")
                        verify_page(driver)

                        if is_captcha_required:
                            if not input_captcha_and_press_submit(driver, name_to_check):
                                logger.warning("[multiserver_type_court_check] Не удалось решить капчу")
                                continue
                        else:
                            try:
                                submit_button = driver.find_element(By.NAME, "Submit")
                                submit_button.click()
                                logger.info("[multiserver_type_court_check] Нажата кнопка 'Submit'")
                            except Exception as e:
                                logger.warning(f"[multiserver_type_court_check] Ошибка при нажатии Submit: {e}")
                                continue

                        html_table = get_all_cases(driver)
                        logger.info(f"[multiserver_type_court_check] Таблица дел получена (длина: {len(html_table)} символов)")

                        court_results[court_name][name_to_check].setdefault(category_name, {})[subcategory["name"]] = html_table
                        logger.success("[multiserver_type_court_check] Результат успешно добавлен")

                        find_and_click_back_btn(driver)
                        logger.info("[multiserver_type_court_check] Выполнен возврат назад")

                        verify_page(driver)
                        find_and_click_change_btn(driver)
                        logger.info("[multiserver_type_court_check] Нажата кнопка 'Изменить'")

                logger.info("=== Конец итерации по имени ===")

    except Exception as e:
        logger.exception(f"[multiserver_type_court_check] Критическая ошибка при проверке: {e}")
        raise

    return court_results

def check_court_availible(driver,address):
    driver.get(address)
    logger.info(f"[check_court_availible] Страница загружена")
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a.menu__link"))
    )
    all_links = driver.find_elements(By.CSS_SELECTOR, "a.menu__link")
    sud_delo_button = None

    for link in all_links:
        href = link.get_attribute("href")
        if "sud_delo" in href:
            sud_delo_button = link
            break

    if sud_delo_button is None:
        logger.error(f"[check_court_availible] Не найдена кнопка 'Судебное делопроизводство' на сайте {address}")
        return {f"Сайт {address}": {"__error__": "Ошибка при работе с судом. Не найдено кнопка судебное делопроизовдство"}}

    logger.info(f"[check_court_availible] Кнопка 'Судебное делопроизводство' найдена — выполняется переход")
    driver.execute_script("arguments[0].scrollIntoView(true);", sud_delo_button)
    time.sleep(0.3)
    sud_delo_button.click()
    try:
        element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".box.box_common.m-all_m")))
        if "Информация временно недоступна" in element.text:
            logger.warning("Сайт не работает. Информация временно недоступна")
            return False
        else:
            logger.success("Сайт работает. Информация доступна")
            return True
    except Exception as e:
        return{f"Сайт {address}": {"__error__": "Ошибка при работе с судом. Информация временно недоступна"}}

def parse_court_yellow(driver, address,fullname):
    logger.info(f"[parse_court_yellow] Запуск параллельной проверки судов по адресу {address}.")
    names = make_name_initials(fullname)
    court_type = get_court_type(driver,address)
    is_court_availible = check_court_availible(driver,address)
    logger.info(f"[parse_court_yellow] Тип суда {court_type}.")
    court_result = {}
    if(court_type == "regular"):
        if(is_court_availible):
            court_result = regular_type_court_check(driver,address,names)
            return court_result 
        return{f"Сайт {address}": {"__error__": "Сайт не работает. Информация временно недоступна"}}
    if(court_type == "modern"):
        if(is_court_availible):
            court_result = modern_type_court_check(driver,address,names)
            return court_result
        return{f"Сайт {address}": {"__error__": "Сайт не работает. Информация временно недоступна"}}
    if(court_type == "multi"):
        if(is_court_availible):
            court_result = multiserver_type_court_check(driver,address,names)
            return court_result
        return{f"Сайт {address}": {"__error__": "Сайт не работает. Информация временно недоступна"}}
    if(court_type == "unavailable"):
        return{f"Сайт {address}": {"__error__": "Ошибка при работе с судом. Сайт не поддерживается"}}
    return {f"Сайт {address}": {"__error__": "Ошибка при работе с судом. Не удалось определить тип суда"}}