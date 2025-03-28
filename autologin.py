from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import os
from dotenv import load_dotenv
from webdriver import get_driver
import pyotp
import parser

# Загрузка данных из файла .env
load_dotenv("database.env")
LOGIN = os.getenv("LOGIN")
PASSWD = os.getenv("PASSWORD")
KEY = os.getenv("KEY")
USER_ID = os.getenv("USER_ID")

def firstlogin():
    totp = pyotp.TOTP(KEY)
    driver = get_driver()
    driver.get("https://dnevnik.egov66.ru")
    
    # Нажимаем "Войти через Госуслуги"
    WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Войти через Госуслуги')]"))).click()
    
    try:
        # Ввод логина
        login = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.ID, "login")))
        login.clear()
        login.send_keys(LOGIN)
    except:
        print("Поле логина не требуется, продолжаем...")
    
    # Ввод пароля
    password = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.ID, "password")))
    password.clear()
    password.send_keys(PASSWD)
    
    # Нажатие кнопки "Войти"
    WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//button[@class='plain-button plain-button_wide']"))).click()
    
    # Ввод кода двухфакторной аутентификации
    current_code = totp.now()
    fa2 = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, "//span[1]//input[1]")))
    fa2.clear()
    fa2.send_keys(current_code)
    
    # Возвращаем драйвер для дальнейшей работы
    return driver

def relogin(driver):
    """Функция для релогина, если токен истёк"""
    totp = pyotp.TOTP(KEY)
    driver.get("https://dnevnik.egov66.ru")
    
    WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Войти через Госуслуги')]"))).click()
    
    # Ввод пароля
    password = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.ID, "password")))
    password.clear()
    password.send_keys(PASSWD)
    
    # Нажатие кнопки "Войти"
    WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//button[@class='plain-button plain-button_wide']"))).click()
    
    # Ввод кода двухфакторной аутентификации
    current_code = totp.now()
    fa2 = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, "//span[1]//input[1]")))
    fa2.clear()
    fa2.send_keys(current_code)

def main():
    driver = firstlogin()
    
    while True:
        try:
            # Запускаем парсер
            parser.changes(driver, USER_ID)
        except Exception as e:
            print(f"Ошибка: {e}. Выполняем релогин...")
            relogin(driver)

# Запуск программы
if __name__ == "__main__":
    main()