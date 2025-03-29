# Dnevnik.egov66.ru parser  
 

тестовый readme.md  
Просто бета тест парсера оценок из электронного дневника в telegram бот. От пользователя требуются минимальные(насколько это в принципе возможно)действия.    
Поскольку дневник не имеет какого либо апи для рапзработчиков, парсим все напрямую при помощи selenium.  
Нужно понимать, электронный дневник является максимально нестабильным, поэтому баги в любом случае будут    
 


 

## Схема работы:  

![изображение](https://github.com/user-attachments/assets/36875bcd-4f7a-461b-b99f-d99c5d3ac089)
 


 
## Структура проекта  
dnevnik-parser-2.0/  
├── [autologin.py](autologin.py)    # Авторизация и управление сессией (клиент)  
├── [parser.py](parser.py)       # Парсинг данных и отправка на сервер (клиент)  
├── [telegram_bot.py](telegram_bot.py) # Telegram-бот для уведомлений (сервер)  
├── [api_server.py](api_server.py)   # API-сервер для обработки данных (сервер)  
├── [webdriver.py](webdriver.py)    # Инициализация базы данных (клиент)  
├── [requirements.txt](requirements.txt) # Зависимости проекта  
├── database.env              # Локальная база данных  (клиент)  
└── README.md                 # Документация проекта  
 


 


 

## Функционал  
- Авторизация на сайте через Госуслуги.
- Парсинг оценок и пропусков.
- Отправка данных на сервер через REST API.
- Уведомление пользователей через Telegram-бот.
- Проверка изменений данных перед отправкой.

​


​


​
