from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import os
from dotenv import load_dotenv
from webdriver import get_driver
import pyotp
import parser
import logging

# Загрузка данных из файла .env
load_dotenv("database.env")
LOGIN = os.getenv("LOGIN")
PASSWD = os.getenv("PASSWORD")
KEY = os.getenv("KEY")
UUID = os.getenv("UUID")


LOGIN_BUTTON_FIRST = "//button[contains(text(),'Войти через Госуслуги')]"
LOGIN_BUTTON_SECOND = "//button[@class='plain-button plain-button_wide']"
CODE2FA = "//span[1]//input[1]"

def login(driver=None):
    """Универсальная функция для входа в систему."""
    logging.info("Запуск функции login.")
    totp = pyotp.TOTP(KEY)
    # Если драйвер не передан, создаём новый
    if driver is None:
        driver = get_driver()
    driver.get("https://dnevnik.egov66.ru")
    try:
        # Нажимаем "Войти через Госуслуги"
        WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, LOGIN_BUTTON_FIRST))).click()
        logging.info("Кнопка 'Войти через Госуслуги' нажата.")
        
        # Ввод логина (только если это первый вход)

        try:
            login = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.ID, "login")))
            login.clear()
            login.send_keys(LOGIN)
            logging.info("Логин введён.")
        except:
            logging.warning("Поле логина не требуется, продолжаем...")
        
        # Ввод пароля
        password = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.ID, "password")))
        password.clear()
        password.send_keys(PASSWD)
        logging.info("Пароль введён.")
        
        # Нажатие кнопки "Войти"
        WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, LOGIN_BUTTON_SECOND))).click()
        logging.info("Кнопка 'Войти' нажата.")
        
        # Ввод кода двухфакторной аутентификации
        current_code = totp.now()
        fa2 = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, CODE2FA)))
        fa2.clear()
        fa2.send_keys(current_code)
        logging.info("Код двухфакторной аутентификации введён.")
        
        return driver
    except Exception as e:
        logging.error(f"Ошибка в функции login: {e}")
        return driver

def main():
    logging.info("Запуск программы.")
    driver = login()  # Первичный вход
    
    while True:
        try:
            # Запускаем парсер
            logging.info("Запуск парсера.")
            parser.check_changes(driver, UUID)
        except Exception as e:
            logging.error(f"Ошибка в main: {e}. Выполняем релогин...")
            driver = login(driver)  # Повторный вход
            continue

# Запуск программы
if __name__ == "__main__":
    main()