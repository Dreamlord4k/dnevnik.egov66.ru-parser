from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time


def parsing(driver):
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
    
    # header_elements = driver.find_elements(By.CLASS_NAME, "_gap0_19hvj_69")
    # dates = [header.get_attribute("textContent").strip() for header in header_elements if header.get_attribute("textContent").strip()]    
    
    rows = driver.find_elements(By.XPATH, "//tr")
    for row in rows:
        try:
            subject = row.find_element(By.CLASS_NAME, "_discipline_875gj_34")
            subject_el = subject.text
            
            grades = row.find_elements(By.CLASS_NAME, "_grade_1qkyu_5")
            grades_el = [grade.get_attribute("textContent").strip() for grade in grades if grade.get_attribute("textContent").strip() != '']
            grades_data[subject_el]= list(map(int, grades_el))
            
            absences = row.find_elements(By.CLASS_NAME, "_gap30_19hvj_93")
            absence_el = [absence.get_attribute("textContent").strip() for absence in absences if absence.get_attribute("textContent").strip() in ['У', 'Н', 'Б']]
            absences_data[subject_el] = len(absence_el)
        except:
            continue
    print(grades_data)
    print(absences_data)
    