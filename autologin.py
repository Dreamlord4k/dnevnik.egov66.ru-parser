from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import os
from dotenv import load_dotenv
from webdriver import get_driver
import pyotp
import parser
load_dotenv("database.env")
LOGIN = os.getenv("LOGIN")
PASSWD = os.getenv("PASSWORD")
KEY = os.getenv("KEY")


def firstlogin():
    totp = pyotp.TOTP(KEY)
    current_code = totp.now()
    driver = get_driver()
    driver.get("https://dnevnik.egov66.ru")
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Войти через Госуслуги')]"))).click()
    try:
        login = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "login")))
        login.clear()
        login.send_keys(LOGIN)
    except: 
        print('значит relogin')
    password = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "password")))
    password.clear()
    password.send_keys(PASSWD)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@class='plain-button plain-button_wide']"))).click()
    fa2 = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//span[1]//input[1]")))
    fa2.clear()
    fa2.send_keys(current_code)
    
    
    parser.parsing(driver)
firstlogin()
