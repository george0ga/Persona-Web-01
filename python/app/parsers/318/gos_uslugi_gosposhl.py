from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from app.utils.logger import logger
import time

link = "https://www.gosuslugi.ru/pay?tab=STATE_DUTY"

def check_gos_uslugi_gosposhl(inn: str, driver) -> str:
    logger.info(f"[check_gos_uslugi_gosposhl] Проверка формата ИНН")
    if not inn.isdigit() or len(inn) not in [10, 12]:
        logger.error(f"[check_gos_uslugi_gosposhl] Неверный формат ИНН (10 или 12 цифр)")
        return "Неверный формат ИНН (10 или 12 цифр)"
    logger.success(f"[check_gos_uslugi_gosposhl] Формат ИНН корректный")
    try:
        logger.info(f"[check_gos_uslugi_gosposhl] Проверка формата ИНН")
        driver.get(link)
        wait = WebDriverWait(driver, 10)
        
        inn_tab = wait.until(EC.element_to_be_clickable((By.ID, "inn")))
        inn_tab.click()
        input_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.text-input")))
        input_field.clear()
        logger.info(f"[check_gos_uslugi_gosposhl] Попытка отправить запрос")
        try:
            for ch in inn:
                input_field.send_keys(ch)
                time.sleep(0.005)
            input_field.send_keys(Keys.ENTER)
            time.sleep(3)
            logger.success(f"[check_gos_uslugi_gosposhl] Запрос успешно отправлен")
        except Exception as e:
            logger.error(f"[check_gos_uslugi_gosposhl] Ошибка при отправке запроса: {e}")
        logger.info(f"[check_gos_uslugi_gosposhl] Попытка парсинга ответа")
        try:
            error_label = driver.find_element(By.CSS_SELECTOR, "#errors_inn label")
            if error_label.is_displayed() and error_label.size['height'] > 0:
                logger.error(f"[check_gos_uslugi_gosposhl] Отправлен некорректный ИНН ФЛ")
                return "Некорректный ИНН ФЛ"
        except NoSuchElementException:
            pass
        
        try:
            h3 = driver.find_element(By.CSS_SELECTOR, "h3.title-h4")
            if "нет неоплаченных начислений" in h3.text.lower():
                logger.success(f"[check_gos_uslugi_gosposhl] По ИНН {inn} нет задолженностей по госпошлинам")
                return f"По ИНН {inn} нет задолженностей по госпошлинам"
        except NoSuchElementException:
            pass
        logger.warning(f"[check_gos_uslugi_gosposhl] По ИНН {inn} найдены задолженности (детали не извлечены")
        return f" По ИНН {inn} найдены задолженности (детали не извлечены)"

    except TimeoutException:
        logger.error(f"[check_gos_uslugi_gosposhl] Ошибка доступа к сайту. Не удалось загрузить элементы.")
        return " Таймаут: элементы не загрузились"
    except Exception as e:
        logger.error(f"[check_gos_uslugi_gosposhl] Ошибка при проверке: {e}.")
        return f" Ошибка при проверке: {e}"
