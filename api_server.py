from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Путь к базе данных
DB_PATH = "big_data.db"

@app.route('/update_grades', methods=['POST'])
def update_grades():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    user_id = data.get("user_id")
    grades = data.get("grades")  # Ожидается словарь {subject: grades}
    absences = data.get("absences")  # Ожидается словарь {subject: absence_count}

    if not user_id or not grades or not absences:
        return jsonify({"error": "Invalid data format"}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Обновление оценок
    for subject, grade_list in grades.items():
        grades_str = " ".join(map(str, grade_list))
        cursor.execute("SELECT grade FROM grades WHERE user_id = ? AND subject = ?", (user_id, subject))
        result = cursor.fetchone()

        if result is None:
            cursor.execute("INSERT INTO grades (user_id, subject, grade) VALUES (?, ?, ?)", (user_id, subject, grades_str))
        elif result[0] != grades_str:
            cursor.execute("UPDATE grades SET grade = ? WHERE user_id = ? AND subject = ?", (grades_str, user_id, subject))

    # Обновление пропусков
    for subject, absence_count in absences.items():
        cursor.execute("SELECT absence_count FROM absences WHERE user_id = ? AND subject = ?", (user_id, subject))
        result = cursor.fetchone()

        if result is None:
            cursor.execute("INSERT INTO absences (user_id, subject, absence_count) VALUES (?, ?, ?)", (user_id, subject, absence_count))
        elif result[0] != absence_count:
            cursor.execute("UPDATE absences SET absence_count = ? WHERE user_id = ? AND subject = ?", (absence_count, user_id, subject))

    conn.commit()
    conn.close()

    return jsonify({"message": "Data updated successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)