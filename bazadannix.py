import sqlite3

def initialize_database():
    # Подключение к базе данных (если файла нет, он будет создан)
    conn = sqlite3.connect("big_data.db")
    cursor = conn.cursor()

    # Создание таблицы для хранения пользователей с UUID
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        uuid TEXT PRIMARY KEY,  -- Уникальный идентификатор пользователя
        telegram_id INTEGER UNIQUE NOT NULL  -- Telegram ID пользователя
    )""")

    # Создание таблицы для хранения данных об оценках
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS grades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uuid TEXT NOT NULL,  -- Привязка к UUID пользователя
        subject TEXT NOT NULL,
        grade TEXT NOT NULL,
        FOREIGN KEY (uuid) REFERENCES users (uuid) ON DELETE CASCADE
    )""")

    # Создание таблицы для хранения данных об отсутствии
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS absences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uuid TEXT NOT NULL,  -- Привязка к UUID пользователя
        subject TEXT NOT NULL,
        absence_count INTEGER NOT NULL,
        FOREIGN KEY (uuid) REFERENCES users (uuid) ON DELETE CASCADE
    )""")

    # Сохранение изменений и закрытие соединения
    conn.commit()
    conn.close()
    print("База данных успешно инициализирована с поддержкой UUID.")

if __name__ == "__main__":
    initialize_database()