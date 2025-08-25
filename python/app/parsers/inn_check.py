from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import time
from app.utils.logger import logger
from app.schemas import ResponseModel  

link = "https://service.nalog.ru/invalid-inn-fl.html"

def check_inn_validity(inn: str, driver) -> str:
    logger.info(f"[check_inn_validity] Проверка валидности ИНН: {inn}")
    if not inn.isdigit() or len(inn) not in [10, 12]:
        logger.error(f"[check_inn_validity] Неверный формат ИНН (10 или 12 цифр)")
        return ResponseModel(
            success=False,
            status="format_error",
            message="Неверный формат ИНН (10 или 12 цифр)"
        )

    try:
        driver.get(link)
        logger.info(f"[check_inn_validity] Попытка отправить запрос")
        try:
            input_elem = driver.find_element(By.ID, "inn")
            input_elem.clear()
            for ch in inn:
                input_elem.send_keys(ch)
                time.sleep(0.005)        
            input_elem.send_keys(Keys.ENTER)
            time.sleep(1)
        except Exception as e:
            logger.error(f"[check_inn_validity] Ошибка при отправке запроса: {e}")
            raise
        logger.success(f"[check_inn_validity] Запрос отправлен")
        logger.info(f"[check_inn_validity] Попытка парсинга ответа")
        try:
            error_label = driver.find_element(By.CSS_SELECTOR, "#errors_inn label")
            if error_label.is_displayed() and error_label.size['height'] > 0:
                logger.error(f"[check_inn_validity] Ответ получен. Введен некоректный ИНН")
                return ResponseModel(
                    success=False,
                    status="invalid",
                    message="Некорректный ИНН ФЛ"
                )
        except NoSuchElementException:
            pass
        if driver.find_element(By.ID, "pnlResult").is_displayed():
            date = driver.find_element(By.ID, "txtDate").text.strip()
            logger.warning(f"[check_inn_validity] Ответ получен. ИНН недействителен (дата: {date})")
            return ResponseModel(
                success=False,
                status="invalid",
                message=f"ИНН {inn} недействителен (дата: {date})"
            )
        else:
            logger.success(f"[check_inn_validity] Ответ получен. ИНН действителен ")
            return ResponseModel(
                success=True,
                status="valid",
                message=f"ИНН {inn} действителен"
            )

    except Exception as e:
        logger.error(f"[check_inn_validity] Не удалось получить ответ от сервиса")
        return ResponseModel(
            success=False,
            status="server_error",
            message=f"Ошибка при проверке ИНН: {e}"
        )
