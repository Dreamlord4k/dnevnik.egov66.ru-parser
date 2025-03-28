import threading
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import os
import aiosqlite
import uuid
from pyrogram.errors import PeerIdInvalid

# Загрузка данных из файла .env
load_dotenv("databasetg.env")
token = os.getenv("TOKEN")
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")

app = Client("DnevnikEgov66_bot",
             api_hash=api_hash,
             api_id=api_id,
             bot_token=token)


async def register_user(telegram_id):
    """Регистрирует пользователя и привязывает UUID к Telegram ID."""
    async with aiosqlite.connect("big_data.db") as conn:
        # Проверяем, существует ли пользователь
        async with conn.execute("SELECT uuid FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            result = await cursor.fetchone()
            if result:
                return result[0], False  # Возвращаем существующий UUID и флаг is_new = False

        # Если пользователь не существует, создаём запись
        user_uuid = str(uuid.uuid4())  # Генерация UUID
        await conn.execute("INSERT INTO users (uuid, telegram_id) VALUES (?, ?)", (user_uuid, telegram_id))
        await conn.commit()
        return user_uuid, True  # Возвращаем новый UUID и флаг is_new = True


async def check_for_updates():
    """Асинхронная функция для проверки изменений в базе данных и отправки уведомлений."""
    print("Функция check_for_updates запущена")  # Отладочное сообщение

    async with aiosqlite.connect("big_data.db") as conn:
        last_grades = {}
        last_absences = {}

        while True:
            print("Начало цикла проверки изменений")  # Отладочное сообщение

            # Проверяем изменения в таблице grades
            async with conn.execute("SELECT uuid, subject, grade FROM grades") as cursor:
                grades = await cursor.fetchall()
                print(f"Текущие оценки из базы: {grades}")  # Отладочное сообщение
                for uuid, subject, grade in grades:
                    if (uuid, subject) not in last_grades or last_grades[(uuid, subject)] != grade:
                        # Если данные изменились, отправляем уведомление
                        print(f"Изменение в оценках: {uuid}, {subject}, {grade}")  # Отладочное сообщение
                        try:
                            async with conn.execute("SELECT telegram_id FROM users WHERE uuid = ?", (uuid,)) as user_cursor:
                                user_result = await user_cursor.fetchone()
                                if user_result:
                                    telegram_id = user_result[0]
                                    asyncio.run_coroutine_threadsafe(
                                        app.send_message(
                                            chat_id=telegram_id,
                                            text=f"Обновлены оценки по предмету **{subject}**: __{grade}__"
                                        ),
                                        asyncio.get_event_loop()
                                    )
                                    last_grades[(uuid, subject)] = grade
                        except PeerIdInvalid:
                            print(f"Ошибка: пользователь с UUID {uuid} не взаимодействовал с ботом.")

            # Проверяем изменения в таблице absences
            async with conn.execute("SELECT uuid, subject, absence_count FROM absences") as cursor:
                absences = await cursor.fetchall()
                print(f"Текущие пропуски из базы: {absences}")  # Отладочное сообщение
                for uuid, subject, absence_count in absences:
                    if (uuid, subject) not in last_absences or last_absences[(uuid, subject)] != absence_count:
                        # Если данные изменились, отправляем уведомление
                        print(f"Изменение в пропусках: {uuid}, {subject}, {absence_count}")  # Отладочное сообщение
                        try:
                            async with conn.execute("SELECT telegram_id FROM users WHERE uuid = ?", (uuid,)) as user_cursor:
                                user_result = await user_cursor.fetchone()
                                if user_result:
                                    telegram_id = user_result[0]
                                    asyncio.run_coroutine_threadsafe(
                                        app.send_message(
                                            chat_id=telegram_id,
                                            text=f"Обновлены пропуски по предмету **{subject}**: __{absence_count}__"
                                        ),
                                        asyncio.get_event_loop()
                                    )
                                    last_absences[(uuid, subject)] = absence_count
                        except PeerIdInvalid:
                            print(f"Ошибка: пользователь с UUID {uuid} не взаимодействовал с ботом.")

            # Задержка перед следующей проверкой
            print("Задержка на 10 секунд")  # Отладочное сообщение
            await asyncio.sleep(10)


def run_check_for_updates():
    """Функция для запуска check_for_updates в отдельном потоке."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(check_for_updates())

@app.on_callback_query()
async def handle_callback_query(client, callback_query):
    """Обработчик нажатий на кнопки."""
    telegram_id = callback_query.from_user.id
    data = callback_query.data  # Получаем данные из callback_data

    # Извлекаем UUID пользователя из базы данных
    async with aiosqlite.connect("big_data.db") as conn:
        async with conn.execute("SELECT uuid FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            result = await cursor.fetchone()
            if not result:
                # Если UUID не найден, отправляем сообщение об ошибке
                await callback_query.answer("Вы не зарегистрированы. Пожалуйста, отправьте сообщение боту.")
                return
            user_uuid = result[0]

        if data == "grades":
            # Проверяем наличие данных об оценках
            async with conn.execute("SELECT subject, grade FROM grades WHERE uuid = ?", (user_uuid,)) as cursor:
                grades = await cursor.fetchall()

            if grades:
                # Если данные есть, отправляем их пользователю
                response = "**Ваши оценки:**\n"
                for subject, grade in grades:
                    if grade.strip():
                        grades_list = list(map(int, grade.split()))
                        avg_grade = round(sum(grades_list) / len(grades_list), 2)
                        response += f"**{subject}:** __{grade}__ | **Cр.балл:** __{avg_grade}__\n\n"
                    else:
                        response += f"**{subject}:** __{grade}__ | **(нет данных для вычисления среднего балла)**\n"
            else:
                # Если данных нет, отправляем сообщение
                response = "На вас нет данных об оценках в базе данных."

        elif data == "absences":
            # Проверяем наличие данных о пропусках
            async with conn.execute("SELECT subject, absence_count FROM absences WHERE uuid = ?", (user_uuid,)) as cursor:
                absences = await cursor.fetchall()

            if absences:
                # Если данные есть, отправляем их пользователю
                response = "**Ваши пропуски:**\n"
                for subject, absence_count in absences:
                    response += f"**{subject}:** __{absence_count}__ пропусков\n"
            else:
                # Если данных нет, отправляем сообщение
                response = "На вас нет данных о пропусках в базе данных."

        else:
            response = "Неизвестная команда."

        # Подтверждаем обработку нажатия кнопки
        await callback_query.answer()
        # Отправляем ответ пользователю
        await client.send_message(
            chat_id=callback_query.message.chat.id,
            text=response
        )

@app.on_message(filters.private)
async def handle_private_message(client, message):
    """Обработчик входящих сообщений."""
    telegram_id = message.from_user.id
    text = message.text.strip().lower().capitalize()
    print(f"Получено сообщение от {telegram_id}: {text}")

    # Регистрируем пользователя и получаем UUID и флаг is_new
    user_uuid, is_new = await register_user(telegram_id)

    if is_new:
        # Отправляем UUID только новым пользователям
        await client.send_message(
            chat_id=message.chat.id,
            text=f"Добро пожаловать! Ваш уникальный идентификатор (UUID): {user_uuid}\n"
                 f"Сохраните его в файл database.env для дальнейшего использования."
        )
        print(f"Пользователь зарегистрирован: Telegram ID = {telegram_id}, UUID = {user_uuid}")

    # Подключение к базе данных
    async with aiosqlite.connect("big_data.db") as conn:
        async with conn.execute("SELECT grade FROM grades WHERE uuid = ? AND subject = ?", (user_uuid, text)) as cursor:
            grades = await cursor.fetchone()

        if grades:
            # Если предмет найден, отправляем список оценок
            grades_list = list(map(int, grades[0].split()))
            response = f"**Ваши оценки по предмету {text.capitalize()}:** __{' '.join(map(str, grades_list))}__\n"
            response += f"**Средний балл:** __{round(sum(grades_list) / len(grades_list), 2)}__"
        else:
            # Если предмет не найден, показываем кнопки
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Оценки", callback_data="grades")],
                [InlineKeyboardButton("Пропуски", callback_data="absences")]
            ])
            response = "Выберите, что вы хотите посмотреть:"
            await client.send_message(
                chat_id=message.chat.id,
                text=response,
                reply_markup=keyboard
            )
            return

        # Отправляем ответ пользователю
        await client.send_message(
            chat_id=message.chat.id,
            text=response
        )


if __name__ == "__main__":
    print("Запуск Telegram-бота")  # Отладочное сообщение

    # Запускаем функцию check_for_updates в отдельном потоке
    threading.Thread(target=run_check_for_updates, daemon=True).start()

    # Запускаем Telegram-бот
    app.run()