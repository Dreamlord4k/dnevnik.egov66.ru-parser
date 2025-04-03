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


TIMEZONE = pytz.timezone('Asia/Yekaterinburg')

SCHEDULE = {
    'MONDAY': [
        {'start': '08:00', 'end': '08:40', 'subject': 'Разговоры о важном'},
        {'start': '08:50', 'end': '09:25'},
        {'start': '09:45', 'end': '10:20'},
        {'start': '10:40', 'end': '11:15'},
        {'start': '11:35', 'end': '12:10'},
        {'start': '12:20', 'end': '12:55'},
        {'start': '13:05', 'end': '13:40'},
        {'start': '14:00', 'end': '14:35'},
    ],
    'TUE_FRI': [
        {'start': '08:00', 'end': '08:40'},
        {'start': '08:50', 'end': '09:30'},
        {'start': '09:50', 'end': '10:30'},
        {'start': '10:50', 'end': '11:30'},
        {'start': '11:50', 'end': '12:30'},
        {'start': '12:40', 'end': '13:20'},
        {'start': '13:30', 'end': '14:10'},
        {'start': '14:30', 'end': '15:10'},
    ]
}

def get_lesson_time():
    """Calculates the time remaining until the end or beginning of the current/next lesson."""
    now_dt = datetime.datetime.now(TIMEZONE)
    now_time = now_dt.time()
    day = now_dt.strftime("%A").upper()

    # Определяем расписание в зависимости от дня
    if day in ['TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY']:
        schedule = SCHEDULE['TUE_FRI']
    elif day == 'MONDAY':
        schedule = SCHEDULE['MONDAY']
    else:
        return "Сегодня нет уроков."

    for i, lesson in enumerate(schedule):
        # Преобразуем время начала и конца урока в объекты time
        start_time = datetime.datetime.strptime(lesson['start'], "%H:%M").time()
        end_time = datetime.datetime.strptime(lesson['end'], "%H:%M").time()

        # Создаем полные datetime объекты для текущего дня с правильной локализацией
        start_dt = TIMEZONE.localize(datetime.datetime.combine(now_dt.date(), start_time))
        end_dt = TIMEZONE.localize(datetime.datetime.combine(now_dt.date(), end_time))
        # Если текущее время находится внутри урока
        if start_time <= now_time < end_time:
            time_left = end_dt - now_dt
            if time_left < datetime.timedelta(0):
                print(f"Ошибка расчета времени: Отрицательное время для урока {i+1}. end_dt={end_dt}, now_dt={now_dt}")
                return "Ошибка в расчете времени (отрицательный результат)."

            minutes_left = int(time_left.total_seconds() / 60)
            subject = lesson.get('subject', f'Урок {i + 1}')
            return f"До конца урока ({subject}): {minutes_left} минут"

        # Если текущее время до начала первого урока
        elif now_time < start_time:
            time_until = start_dt - now_dt
            minutes_until = int(time_until.total_seconds() / 60)
            subject = lesson.get('subject', f'Урок {i + 1}')
            return f"До начала урока ({subject}): {minutes_until} минут"

    # Если время после последнего урока
    last_lesson_end = datetime.datetime.strptime(schedule[-1]['end'], "%H:%M").time()
    if now_time >= last_lesson_end:
        return "Уроки на сегодня закончились."

    return "Ошибка в расчете времени."



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
                # print(f"Текущие оценки из базы: {grades}")  # Отладочное сообщение
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
                    previous_grades_list = last_grades.get((uuid, subject), [])
                    # Сравниваем наборы оценок для обнаружения любых изменений
                    current_grades_set = set(current_grades)
                    previous_grades_set = set(previous_grades_list)

                    if current_grades_set != previous_grades_set:
                        added_grades = list(current_grades_set - previous_grades_set)
                        removed_grades = list(previous_grades_set - current_grades_set)

                        message_parts = [f"Изменения по предмету **{subject}**:"]
                        if added_grades:
                            message_parts.append(f"Добавлены оценки: __{' '.join(map(str, sorted(added_grades)))}__")
                        if removed_grades:
                            message_parts.append(f"Удалены оценки: __{' '.join(map(str, sorted(removed_grades)))}__")
                        # Fallback if sets differ but no specific add/remove detected (e.g., order change only, though unlikely with sets)
                        if not added_grades and not removed_grades:
                             grades_text = ' '.join(map(str, current_grades)) if current_grades else '(оценок нет)'
                             message_parts.append(f"Текущие оценки: __{grades_text}__")

                        notification_text = "\n".join(message_parts)
                        print(f"Отправка уведомления: {notification_text}") # Отладочное сообщение

                        try:
                            async with conn.execute("SELECT telegram_id FROM users WHERE uuid = ?", (uuid,)) as user_cursor:
                                user_result = await user_cursor.fetchone()
                                if user_result:
                                    telegram_id = user_result[0]
                                    asyncio.run_coroutine_threadsafe(
                                        app.send_message(
                                            chat_id=telegram_id,
                                            text=notification_text
                                        ),
                                        asyncio.get_event_loop()
                                    )
                        except PeerIdInvalid:
                            print(f"Ошибка: пользователь с UUID {uuid} не взаимодействовал с ботом.")

                    # Обновляем кэш ВСЕГДА после обработки записи, чтобы отразить текущее состояние из БД
                    last_grades[(uuid, subject)] = current_grades

            # Проверяем изменения в таблице absences
            async with conn.execute("SELECT uuid, subject, absence_count FROM absences") as cursor:
                absences = await cursor.fetchall()
                # print(f"Текущие пропуски из базы: {absences}")  # Отладочное сообщение
                for uuid, subject, absence_count in absences:
                    previous_absence_count = last_absences.get((uuid, subject), None) # Используем None как маркер отсутствия записи
                    # Проверяем, изменилось ли количество пропусков
                    if previous_absence_count is None or previous_absence_count != absence_count:
                        # Отправляем уведомление только если это не первая проверка для этого предмета ИЛИ если значение изменилось
                        if previous_absence_count is not None:
                             print(f"Изменение в пропусках: {uuid}, {subject}, было {previous_absence_count}, стало {absence_count}") # Отладочное сообщение
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
                             except PeerIdInvalid:
                                 print(f"Ошибка: пользователь с UUID {uuid} не взаимодействовал с ботом.")
                    # Обновляем кэш ВСЕГДА после обработки записи
                    last_absences[(uuid, subject)] = absence_count

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
            text=f"Добро пожаловать! Ваш уникальный идентификатор (UUID): ||{user_uuid}||\n"
                 f"Сохраните его в файл database.env для дальнейшего использования.\n"
                 f"Без настройки и запуска самого парсера вы сможете только узнавать время до конца/начала урока)"
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