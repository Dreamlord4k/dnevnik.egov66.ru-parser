# Dnevnik.egov66.ru parser  
   
Просто бета тест парсера оценок из электронного дневника в telegram бот.   
От пользователя требуются минимальные(насколько это в принципе возможно) действия.  
Поскольку дневник не имеет какого либо api для разработчиков, парсим все напрямую при помощи selenium, именно поэтому установка может показаться непростой.    
  
Нужно понимать, что данный электронный дневник является максимально нестабильным, поэтому баги в любом случае будут)   
 


 

## Общая схема работы:  

![изображение](https://github.com/user-attachments/assets/8001f5da-d9ed-4d22-a462-17bfc39c6a25)


 
## Структура проекта  
dnevnik-parser-2.0/  
├── [autologin.py](autologin.py)    # Авторизация и управление сессией (клиент)  
├── [parser.py](parser.py)       # Парсинг данных и отправка на сервер (клиент)  
├── [telegram_bot.py](telegram_bot.py) # Telegram-бот для уведомлений (сервер)  
├── [api_server.py](api_server.py)   # API-сервер для обработки данных (сервер)  
├── [webdriver.py](webdriver.py)    # Инициализация базы данных (клиент)  
├── [requirements.txt](requirements.txt) # Зависимости проекта  
├── [database.env](database.env)              # Локальная база данных  (клиент)  
├── parser.log #логи парсера. Сюда будут выводиться все ошибки  
└── [README.md](README.md)                 # Документация проекта  
 
  
## Функционал  
- Авторизация на сайте через Госуслуги.  
- Парсинг оценок и пропусков.  
- Отправка данных на сервер через REST API.  
- Уведомление пользователей через Telegram-бот.  
- Проверка изменений данных перед отправкой.  



## Как пользоваться?  
  
# 0. **Настраиваем Gosuslugi**
Будет необходимо зайти в настройки gosuslug и изменить метод двухэтапной аутентификации:
![NVIDIA_Overlay_6RLsfMkxQc](https://github.com/user-attachments/assets/e9479028-0a24-45d0-9eef-112e608d9e37)
После чего скопировать ключ:
![NVIDIA_Overlay_ZJ8UXgnUIc](https://github.com/user-attachments/assets/6510eab9-a354-4938-a837-567314b45986)
в базу данных [database.env](database.env) в строку KEY

# 1. **Установка Python и pip**
Убедитесь, что у вас установлен Python версии 3.10 или выше.  
Если Python не установлен, скачайте его с официального сайта Python и установите.  
Во время установки убедитесь, что вы отметили галочку Add Python to PATH.    
Проверьте, что Python установлен, выполнив команду в терминале:  
```
python --version
```
Проверьте, установлен ли pip, выполнив команду:
```
pip --version
```
Если pip не установлен, установите его с помощью команды:
```
python -m ensurepip --upgrade
```
# 2. **Установка парсера**
Для установки парсера просто скачайте последний доступный архив из [reliases](https://github.com/Dreamlord4k/dnevnik.egov66.ru-parser/releases).  
После чего распакуйте архив в любую удобную вам папку.  
  
# 3. **Настройка файла database.env**
   1. В папке проекта найдите файл [database1.env](database.env).   
   2. Откройте его в любом текстовом редакторе (например, Блокнот).    
   3. Заполните файл своими данными:   
   **LOGIN:** ваш логин для входа в электронный дневник.  
   **PASSWORD:** ваш пароль от входа в электронный дневник.  
   **KEY:** секретный ключ для генерации 2FA-кодов (TOTP).  
   **UUID** уникальный идентификатор пользователя (который вы получили, написав боту).  
   4. Сохраните изменения и закройте файл.  
  
# 4. **Запуск парсера**
После настройки файла [database.env](database.env) просто запустите файл start.cmd  
Этот файл автоматически создаст виртуальное окружение, установит все зависимости и запустит парсер.  

Если вы хотите выполнить эти шаги вручную:  
 1. Откройте терминал (или командную строку) в папке проекта.  
 2. Создайте виртуальное окружение:  
    ```
    python -m venv venv
    ```  
 3. Активируйте виртуальное окружение:
    Windows:
       ```  
       venv\Scripts\activate
       ```  
    Linux/MacOS:
       ```  
       source venv/bin/activate
       ```  
 4. Установите зависимости из файла [requirements.txt](requirements.txt):
    ```  
    pip install -r requirements.txt  
    ```
# Syntax Parser. Все права защищены.  
