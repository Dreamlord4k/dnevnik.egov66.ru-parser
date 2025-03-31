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
    level=logging.INFO,  # Уровень логирования (DEBUG, ERROR, DEBUG и т.д.)
    format="%(asctime)s - %(levelname)s - %(message)s"  # Формат логов
)
# Дублируем логи в консоль
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logging.getLogger().addHandler(console_handler)
print('работаем, наверное....')
# Загрузка UUID из файла database.env
load_dotenv("database.env")
UUID = os.getenv("UUID")  # Убедитесь, что UUID добавлен в .env файл
URL = os.getenv("URL")  # URL четверти/полугодия, которое вы хотите парсить

# URL API сервера
SERVER_URL = "https://dream.zeo.lol/update_grades"  # Замените <SERVER_IP> на IP-адрес сервера(не трогать, если вы просто клиент)

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

def parse(driver):
    """Парсинг данных с сайта."""
    try:
        if not driver.current_url.startswith('https://dnevnik.egov66.ru/'):
            time.sleep(2)
        
        target_url = URL
        driver.get(target_url)
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "_discipline_875gj_34")))
        grades_data = {}
        absences_data = {}
        
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

def check_changes(driver, uuid):
    """Проверка изменений и отправка данных на сервер."""
    previous_grades_data = {}
    previous_absences_data = {}

    while True:
        try:
            grades_data, absences_data = parse(driver)

            # Проверяем, изменились ли данные
            if grades_data != previous_grades_data or absences_data != previous_absences_data:
                logging.info("Обнаружены изменения, отправка данных на сервер...")
                send_data_to_server(uuid, grades_data, absences_data)

                # Обновляем предыдущие данные
                previous_grades_data = grades_data
                previous_absences_data = absences_data


            # Задержка на 10 секунд
            print('изменения в оценках не обнаружены')
            time.sleep(30)
        except Exception as e:
            logging.error(f"Ошибка в функции changes: {e}")