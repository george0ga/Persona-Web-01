import tempfile, uuid, shutil

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from loguru import logger

def create_driver(page_load_strategy="normal",headless = True):
    user_agent = UserAgent()
    options = webdriver.ChromeOptions()
    options.page_load_strategy = page_load_strategy
    options.add_argument(f"user-agent={user_agent.random}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--log-level=3")
    if headless:
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        
    logger.info(f" Создание Chrome-драйвера (headless={headless}, strategy='{page_load_strategy}')")
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        logger.success(" Драйвер успешно создан")
        return driver
    except Exception as e:
        logger.exception(f" Ошибка при создании драйвера: {e}")
        raise
