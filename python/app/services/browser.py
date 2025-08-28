from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from loguru import logger
import os

def random_user_agent():
    try:
        from fake_useragent import UserAgent
        return UserAgent().random
    except Exception:
        return ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")

def create_driver(page_load_strategy="normal", headless=True):
    opts = Options()
    opts.page_load_strategy = page_load_strategy
    opts.add_argument(f"--user-agent={random_user_agent()}")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--ignore-certificate-errors")
    opts.add_argument("--log-level=3")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--disable-gpu")

    chromium_bin = os.getenv("CHROME_BIN", "/usr/bin/chromium")
    if os.path.exists(chromium_bin):
        opts.binary_location = chromium_bin

    logger.info(f"Создание Chrome-драйвера (headless={headless}, strategy='{page_load_strategy}')")
    try:
        driver = webdriver.Chrome(options=opts)
        logger.success("Драйвер создан через Selenium Manager")
        return driver
    except Exception as e1:
        logger.warning(f"Selenium Manager не смог запуститься: {e1}. Пытаюсь через webdriver_manager…")

    try:
        from webdriver_manager.chrome import ChromeDriverManager
        from webdriver_manager.core.utils import ChromeType
        service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        driver = webdriver.Chrome(service=service, options=opts)
        logger.success("Драйвер создан через webdriver_manager (Chromium)")
        return driver
    except Exception as e2:
        logger.exception(f"Ошибка при создании драйвера: {e2}")
        raise
