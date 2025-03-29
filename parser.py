import logging
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
import os
import time
import requests

# Настройка логирования
logging.basicConfig(
    filename="parser.log",  # Имя файла для логов
    encoding='utf-8',  # Кодировка файла логов
    level=logging.INFO,  # Уровень логирования (INFO, ERROR, DEBUG и т.д.)
    format="%(asctime)s - %(levelname)s - %(message)s"  # Формат логов
)
print('работаем, наверное....')
# Загрузка UUID из файла database.env
load_dotenv("database.env")
UUID = os.getenv("UUID")  # Убедитесь, что UUID добавлен в .env файл

# URL API сервера
SERVER_URL = "https://dream.zeo.lol/update_grades"  # Замените <SERVER_IP> на IP-адрес сервера

def send_data_to_server(uuid, grades_data, absences_data):
    """Отправка данных на сервер через REST API."""
    payload = {
        "uuid": uuid,
        "grades": grades_data,
        "absences": absences_data
    }

    try:
        response = requests.post(SERVER_URL, json=payload)
        if response.status_code == 200:
            logging.info("Данные успешно отправлены на сервер")
        else:
            logging.error(f"Ошибка при отправке данных: {response.status_code}, {response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка соединения с сервером: {e}")

def parsing(driver):
    """Парсинг данных с сайта."""
    try:
        time.sleep(4)
        if not driver.current_url.startswith('https://dnevnik.egov66.ru/'):
            time.sleep(2)
        
        target_url = 'https://dnevnik.egov66.ru/diary/grades-page/?grades-page-filter=%7B%22values%22%3A%7B%22period%22%3A%2201955f9b-3ed2-7300-badd-40c03a3c97e3%22%2C%22gradeId%22%3A%22019077a2-49f4-76e5-b4d4-ff43a843abbf%22%2C%22discipline%22%3A%2200000000-0000-0000-0000-000000000000%22%2C%22year%22%3A%222024%22%2C%22groupId%22%3Anull%7D%7D'
        driver.get(target_url)
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "_discipline_875gj_34")))
        grades_data = {}
        absences_data = {}
        time.sleep(3)
        
        rows = driver.find_elements(By.XPATH, "//tr")
        for row in rows:
            try:
                subject = row.find_element(By.CLASS_NAME, "_discipline_875gj_34").text
                
                # Извлекаем оценки
                grades = row.find_elements(By.CLASS_NAME, "_grade_1qkyu_5")
                grades_el = [grade.get_attribute("textContent").strip() for grade in grades if grade.get_attribute("textContent").strip() != '']
                grades_data[subject] = list(map(int, grades_el))
                
                # Извлекаем пропуски
                absences = row.find_elements(By.CLASS_NAME, "_gap30_19hvj_93")
                absence_el = [absence.get_attribute("textContent").strip() for absence in absences if absence.get_attribute("textContent").strip() in ['У', 'Н', 'Б']]
                absences_data[subject] = len(absence_el)
            except:
                continue
        
        return grades_data, absences_data
    except Exception as e:
        logging.error(f"Ошибка в функции parsing: {e}")
        return {}, {}

def changes(driver, uuid):
    """Проверка изменений и отправка данных на сервер."""
    previous_grades_data = {}
    previous_absences_data = {}

    while True:
        try:
            grades_data, absences_data = parsing(driver)

            # Проверяем, изменились ли данные
            if grades_data != previous_grades_data or absences_data != previous_absences_data:
                logging.info("Обнаружены изменения, отправка данных на сервер...")
                send_data_to_server(uuid, grades_data, absences_data)

                # Обновляем предыдущие данные
                previous_grades_data = grades_data
                previous_absences_data = absences_data
            else:
                logging.info("Изменений нет, данные не отправлены.")

            # Задержка на 10 секунд
            time.sleep(10)
        except Exception as e:
            logging.error(f"Ошибка в функции changes: {e}")