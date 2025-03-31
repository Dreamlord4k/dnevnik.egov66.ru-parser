import threading
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import os
import aiosqlite
import uuid
from pyrogram.errors import PeerIdInvalid
import pytz
import datetime
TIMEZONE = pytz.timezone('Asia/Yekaterinburg')
# Загрузка данных из файла .env
load_dotenv("databasetg.env")
token = os.getenv("TOKEN")
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")

app = Client("DnevnikEgov66_bot",
             api_hash=api_hash,
             api_id=api_id,
             bot_token=token)


SCHEDULE = {
   'MONDAY': [
       {'start': '08:00', 'end': '08:40', 'subject': 'Разговоры о важном', 'break_after': 10},
       {'start': '08:50', 'end': '09:25', 'break_after': 20},
       {'start': '09:45', 'end': '10:20', 'break_after': 20},
       {'start': '10:40', 'end': '11:15', 'break_after': 20},
       {'start': '11:35', 'end': '12:10', 'break_after': 10},
       {'start': '12:20', 'end': '12:55', 'break_after': 10},
       {'start': '13:05', 'end': '13:40', 'break_after': 20},
       {'start': '14:00', 'end': '14:35', 'break_after': 0}, # no break after last lesson
   ],
   'TUE_FRI': [
       {'start': '08:00', 'end': '08:40', 'break_after': 10},
       {'start': '08:50', 'end': '09:30', 'break_after': 20},
       {'start': '09:50', 'end': '10:30', 'break_after': 20},
       {'start': '10:50', 'end': '11:30', 'break_after': 20},
       {'start': '11:50', 'end': '12:30', 'break_after': 10},
       {'start': '12:40', 'end': '13:20', 'break_after': 10},
       {'start': '13:30', 'end': '14:10', 'break_after': 20},
       {'start': '14:30', 'end': '15:10', 'break_after': 0}, # no break after last lesson
   ]
}


def get_lesson_time():
    """Calculates the time remaining until the end or beginning of the current/next lesson."""
    now = datetime.datetime.now(TIMEZONE)
    current_time = now.strftime("%H:%M")
    day = now.strftime("%A").upper()

    if day in ['TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY']:
        schedule = SCHEDULE['TUE_FRI']
    elif day == 'MONDAY':
        schedule = SCHEDULE['MONDAY']
    else:
        return "Сегодня нет уроков."

    for i, lesson in enumerate(schedule):
        start_time = lesson['start']
        end_time = lesson['end']
        break_after = lesson.get('break_after', 0)

        if current_time < start_time:
            # Time until the beginning of the lesson
            lesson_start_time = datetime.datetime.strptime(start_time, "%H:%M").time()
            lesson_start_datetime = datetime.datetime.combine(now.date(), lesson_start_time, tzinfo=TIMEZONE)
            time_remaining = lesson_start_datetime - now
            minutes = time_remaining.total_seconds() / 60
            return f"До начала урока {i+1}: {int(minutes)} минут"

        elif current_time >= start_time and current_time <= end_time:
            # Time until the end of the lesson
            lesson_end_time = datetime.datetime.strptime(end_time, "%H:%M").time()
            lesson_end_datetime = datetime.datetime.combine(now.date(), lesson_end_time, tzinfo=TIMEZONE)
            time_remaining = lesson_end_datetime - now
            minutes = time_remaining.total_seconds() / 60
            return f"До конца урока {i+1}: {int(minutes)} минут"

    # If the current time is after all lessons
    return "Уроки закончились."


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
                    # --- Validation Start ---
                    if not isinstance(uuid, str) or not uuid:
                        print(f"Ошибка валидации: Неверный формат UUID '{uuid}' для предмета '{subject}'. Пропускаем строку.")
                        continue
                    if not isinstance(subject, str) or not subject:
                        print(f"Ошибка валидации: Неверный формат предмета '{subject}' для UUID '{uuid}'. Пропускаем строку.")
                        continue
                    if not isinstance(grade, str):
                        print(f"Ошибка валидации: Оценка должна быть строкой, получено '{type(grade)}' для UUID '{uuid}', предмет '{subject}'. Пропускаем строку.")
                        continue

                    current_grades = []
                    try:
                        current_grades = list(map(int, grade.split()))  # Преобразуем строку в список оценок
                    except ValueError:
                        print(f"Ошибка валидации: Неверный формат оценки '{grade}' для UUID '{uuid}', предмет '{subject}'. Содержит нечисловые значения. Пропускаем строку.")
                        continue
                    previous_grades = last_grades.get((uuid, subject), [])
                    # Определяем новые оценки
                    new_grades = [g for g in current_grades if g not in previous_grades]
                    if new_grades:
                        print(f"Новые оценки по предмету {subject}: {new_grades}")  # Отладочное сообщение
                        try:
                            async with conn.execute("SELECT telegram_id FROM users WHERE uuid = ?", (uuid,)) as user_cursor:
                                user_result = await user_cursor.fetchone()
                                if user_result:
                                    telegram_id = user_result[0]
                                    asyncio.run_coroutine_threadsafe(
                                        app.send_message(
                                            chat_id=telegram_id,
                                            text=f"Новые оценки по предмету **{subject}**: __{' '.join(map(str, new_grades))}__"
                                        ),
                                        asyncio.get_event_loop()
                                    )
                                    last_grades[(uuid, subject)] = current_grades  # Обновляем кэш
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
            if data == "lesson_time":
                response = get_lesson_time()
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
    text = message.text.strip().lower()
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
        async with conn.execute("SELECT subject, grade FROM grades WHERE uuid = ?", (user_uuid,)) as cursor:
            all_user_grades = await cursor.fetchall()

        found_grades_str = None
        found_subject = None
        # Выполняем сравнение без учета регистра в Python
        for db_subject, db_grade in all_user_grades:
            # Сравниваем строчные и удаленные символы из базы данных с введенным строчным текстом
            if db_subject and isinstance(db_subject, str) and db_subject.strip().lower() == text:
                found_grades_str = db_grade
                found_subject = db_subject # сохраним оригинальное название предмета
                break # выход из цикла, если нашли совпадение

        if found_grades_str is not None:
            # Если предмет найден, отправляем список оценок
            grades_list = []
            response = f"**Ваши оценки по предмету {found_subject}:** " # используем оригинальное название предмета
            if found_grades_str and isinstance(found_grades_str, str) and found_grades_str.strip():
                try:
                    grades_list = list(map(int, found_grades_str.split()))
                    response += f"__{' '.join(map(str, grades_list))}__\n"
                    # вычисляем средний балл
                    if grades_list:
                        avg_grade = round(sum(grades_list) / len(grades_list), 2)
                        response += f"**Средний балл:** __{avg_grade}__"
                    else:
                         response += '\nнет данных для вычисления среднего балла'
                except ValueError:
                     response += f"__(ошибка формата: {found_grades_str})__\n" 
                     response += 'нет данных для вычисления среднего балла'
            else:
                 response += f"__(нет оценок)__\n"
                 response += 'нет данных для вычисления среднего балла'
        else:
            # Если предмет не найден, показываем кнопки
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Оценки", callback_data="grades")],
                [InlineKeyboardButton("Пропуски", callback_data="absences")],
                [InlineKeyboardButton("Время до урока", callback_data="lesson_time")]
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