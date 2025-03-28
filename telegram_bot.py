import threading
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import os
import aiosqlite
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


async def check_for_updates():
    """Асинхронная функция для проверки изменений в базе данных и отправки уведомлений."""
    print("Функция check_for_updates запущена")  # Отладочное сообщение

    async with aiosqlite.connect("big_data.db") as conn:
        last_grades = {}
        last_absences = {}

        while True:
            print("Начало цикла проверки изменений")  # Отладочное сообщение

            # Проверяем изменения в таблице grades
            async with conn.execute("SELECT user_id, subject, grade FROM grades") as cursor:
                grades = await cursor.fetchall()
                print(f"Текущие оценки из базы: {grades}")  # Отладочное сообщение
                for user_id, subject, grade in grades:
                    if (user_id, subject) not in last_grades or last_grades[(user_id, subject)] != grade:
                        # Если данные изменились, отправляем уведомление
                        print(f"Изменение в оценках: {user_id}, {subject}, {grade}")  # Отладочное сообщение
                        try:
                            asyncio.run_coroutine_threadsafe(
                                app.send_message(
                                    chat_id=user_id,
                                    text=f"Обновлены оценки по предмету **{subject}**: __{grade}__"
                                ),
                                asyncio.get_event_loop()
                            )
                            last_grades[(user_id, subject)] = grade
                        except PeerIdInvalid:
                            print(f"Ошибка: пользователь с user_id {user_id} не взаимодействовал с ботом.")

            # Проверяем изменения в таблице absences
            async with conn.execute("SELECT user_id, subject, absence_count FROM absences") as cursor:
                absences = await cursor.fetchall()
                print(f"Текущие пропуски из базы: {absences}")  # Отладочное сообщение
                for user_id, subject, absence_count in absences:
                    if (user_id, subject) not in last_absences or last_absences[(user_id, subject)] != absence_count:
                        # Если данные изменились, отправляем уведомление
                        print(f"Изменение в пропусках: {user_id}, {subject}, {absence_count}")  # Отладочное сообщение
                        try:
                            asyncio.run_coroutine_threadsafe(
                                app.send_message(
                                    chat_id=user_id,
                                    text=f"Обновлены пропуски по предмету **{subject}**: __{absence_count}__"
                                ),
                                asyncio.get_event_loop()
                            )
                            last_absences[(user_id, subject)] = absence_count
                        except PeerIdInvalid:
                            print(f"Ошибка: пользователь с user_id {user_id} не взаимодействовал с ботом.")

            # Задержка перед следующей проверкой
            print("Задержка на 10 секунд")  # Отладочное сообщение
            await asyncio.sleep(10)

def run_check_for_updates():
    """Функция для запуска check_for_updates в отдельном потоке."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(check_for_updates())

@app.on_message(filters.private)
async def handle_private_message(client, message):
    """Обработчик входящих сообщений."""
    user_id = message.from_user.id
    text = message.text.strip().lower().capitalize()
    print(f"Получено сообщение от {user_id}: {text}")

    # Подключение к базе данных
    async with aiosqlite.connect("big_data.db") as conn:
        async with conn.execute("SELECT grade FROM grades WHERE user_id = ? AND subject = ?", (user_id, text)) as cursor:
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

@app.on_callback_query()
async def handle_callback_query(client, callback_query):
    """Обработчик нажатий на кнопки."""
    user_id = callback_query.from_user.id
    data = callback_query.data  # Получаем данные из callback_data

    # Подключение к базе данных
    async with aiosqlite.connect("big_data.db") as conn:
        if data == "grades":
            # Получаем оценки пользователя
            async with conn.execute("SELECT subject, grade FROM grades WHERE user_id = ?", (user_id,)) as cursor:
                grades = await cursor.fetchall()

            if grades:
                response = "Ваши оценки:\n"
                for subject, grade in grades:
                    if grade.strip():
                        grades_list = list(map(int, grade.split()))
                        avg_grade = round(sum(grades_list) / len(grades_list), 2)
                        response += f"**{subject}:** __{grade}__ | **Cр.балл:** __{avg_grade}__\n\n"
                    else:
                        response += f"**{subject}:** __{grade}__ | **(нет данных для вычисления среднего балла)**\n"
            else:
                response = "**Вас нет в базе данных.**"

        elif data == "absences":
            # Получаем пропуски пользователя
            async with conn.execute("SELECT subject, absence_count FROM absences WHERE user_id = ?", (user_id,)) as cursor:
                absences = await cursor.fetchall()

            if absences:
                response = "**Ваши пропуски:**\n"
                for subject, absence_count in absences:
                    if absence_count > 0:
                        response += f"**{subject}:** __{absence_count}__\n"
                    else:
                        response += f"**{subject}:** по данному предмету нет пропусков\n"
            else:
                response = "**Пропуски для вашего user_id не найдены.**"

        # Подтверждаем обработку нажатия кнопки
        await callback_query.answer()

        # Отправляем ответ пользователю
        await client.send_message(
            chat_id=callback_query.message.chat.id,
            text=response
        )

        # Удаляем сообщение с кнопками
        await client.delete_messages(chat_id=callback_query.message.chat.id, message_ids=callback_query.message.id)

if __name__ == "__main__":
    print("Запуск Telegram-бота")  # Отладочное сообщение

    # Запускаем функцию check_for_updates в отдельном потоке
    threading.Thread(target=run_check_for_updates, daemon=True).start()

    # Запускаем Telegram-бот
    app.run()