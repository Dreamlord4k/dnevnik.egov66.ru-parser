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

    uuid = data.get("uuid")  # Ожидаем UUID
    grades = data.get("grades")  # Ожидается словарь {subject: grades}
    absences = data.get("absences")  # Ожидается словарь {subject: absence_count}

    if not uuid or not grades or not absences:
        return jsonify({"error": "Invalid data format"}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Обновление оценок
    for subject, grade_list in grades.items():
        grades_str = " ".join(map(str, grade_list))
        cursor.execute("SELECT grade FROM grades WHERE uuid = ? AND subject = ?", (uuid, subject))
        result = cursor.fetchone()

        if result is None:
            cursor.execute("INSERT INTO grades (uuid, subject, grade) VALUES (?, ?, ?)", (uuid, subject, grades_str))
        elif result[0] != grades_str:
            cursor.execute("UPDATE grades SET grade = ? WHERE uuid = ? AND subject = ?", (grades_str, uuid, subject))
        conn.commit()
    # Обновление пропусков
    for subject, absence_count in absences.items():
        cursor.execute("SELECT absence_count FROM absences WHERE uuid = ? AND subject = ?", (uuid, subject))
        result = cursor.fetchone()

        if result is None:
            cursor.execute("INSERT INTO absences (uuid, subject, absence_count) VALUES (?, ?, ?)", (uuid, subject, absence_count))
        elif result[0] != absence_count:
            cursor.execute("UPDATE absences SET absence_count = ? WHERE uuid = ? AND subject = ?", (absence_count, uuid, subject))
        conn.commit()
    conn.commit()
    conn.close()

    return jsonify({"message": "Data updated successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8880)