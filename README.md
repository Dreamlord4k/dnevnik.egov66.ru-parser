# Dnevnik.egov66.ru parser
тестовый readme.md

Просто бета тест парсера оценок из электронного дневника в telegram бот. От пользователя требуются минимальные(насколько это в принципе возможно)действия.
Поскольку дневник не имеет какого либо апи для рапзработчиков, парсим все напрямую при помощи selenium.
а еще,электронный дневник является максимально нестабильным, поэтому баги в любом случае будут)

Схема работы парсера представлена ниже:
![изображение](https://github.com/user-attachments/assets/36875bcd-4f7a-461b-b99f-d99c5d3ac089)





Структура проекта:
dnevnik.egov66.ru-parser/
├── [autologin.py] # Авторизация и управление сессией
├── [parser.py] # Парсинг данных и отправка на сервер
├── [telegram_bot.py](запущен на сервере) # Telegram-бот для уведомлений
├── [api_server.py](запущен на сервере) # API-сервер для обработки данных
├── [webdriver.py] # Конфигурация сессии selenium
├── [requirements.txt]  # Зависимости проекта
├── database.env # Конфиденциальные данные
└── README.md # Документация проекта

## Функционал
- Авторизация на сайте через Госуслуги.
- Парсинг оценок и пропусков.
- Отправка данных на сервер через REST API.
- Уведомление пользователей через Telegram-бот.
- Проверка изменений данных перед отправкой.
