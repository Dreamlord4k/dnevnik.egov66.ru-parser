from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
import os
import time
import sqlite3

# Загрузка user_id из файла database.env
load_dotenv("database.env")
USER_ID = os.getenv("USER_ID")

def base(driver):
    # Подключение к существующей базе данных
    conn = sqlite3.connect("big_data.db")
    cursor = conn.cursor()

    # Переход к обработке изменений
    changes(driver, conn, cursor, USER_ID)

    # Закрытие соединения
    conn.close()

def parsing(driver, conn, cursor, user_id):
    print('сработало')
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

def changes(driver, conn, cursor, user_id):
    
    while True:
        print("Проверка изменений...")
        grades_data, absences_data = parsing(driver, conn, cursor, user_id)
        
        # Обновление оценок
        for subject, grades in grades_data.items():
            grades_str = " ".join(map(str, grades))
            cursor.execute("SELECT grade FROM grades WHERE user_id = ? AND subject = ?", (user_id, subject))
            result = cursor.fetchone()
            
            if result is None:
                # Добавляем новую запись
                cursor.execute("INSERT INTO grades (user_id, subject, grade) VALUES (?, ?, ?)", (user_id, subject, grades_str))
                print(f"Добавлены новые оценки по предмету {subject}: {grades_str}")
            elif result[0] != grades_str:
                # Обновляем существующую запись
                cursor.execute("UPDATE grades SET grade = ? WHERE user_id = ? AND subject = ?", (grades_str, user_id, subject))
                print(f"Обновлены оценки по предмету {subject}: {grades_str}")
        
        # Обновление пропусков
        for subject, absence_count in absences_data.items():
            cursor.execute("SELECT absence_count FROM absences WHERE user_id = ? AND subject = ?", (user_id, subject))
            result = cursor.fetchone()
            
            if result is None:
                # Добавляем новую запись
                cursor.execute("INSERT INTO absences (user_id, subject, absence_count) VALUES (?, ?, ?)", (user_id, subject, absence_count))
                print(f"Добавлены новые пропуски по предмету {subject}: {absence_count}")
            elif result[0] != absence_count:
                # Обновляем существующую запись
                cursor.execute("UPDATE absences SET absence_count = ? WHERE user_id = ? AND subject = ?", (absence_count, user_id, subject))
                print(f"Обновлены пропуски по предмету {subject}: {absence_count}")
        
        # Сохранение изменений в базе данных
        conn.commit()
        
        # Задержка на 10 секунд
        time.sleep(10)