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

@app.route('/get_grades', methods=['GET'])
def get_grades():
    uuid = request.args.get('uuid')
    if not uuid:
        return jsonify({"error": "UUID parameter is required"}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Получение оценок
    cursor.execute("SELECT subject, grade FROM grades WHERE uuid = ?", (uuid,))
    grades_data = cursor.fetchall()
    grades_result = {}
    for subject, grade_str in grades_data:
        # grades_result[subject] = [int(g) for g in grade_str.split()]
        grades_result[subject] = grade_str

    # Получение пропусков
    cursor.execute("SELECT subject, absence_count FROM absences WHERE uuid = ?", (uuid,))
    absences_data = cursor.fetchall()
    absences_result = dict(absences_data)

    conn.close()

    if not grades_result and not absences_result:
        return jsonify({"message": "No data found for this UUID"}), 404
    print('данные посланы')
    return jsonify({
        "uuid": uuid,
        "grades": grades_result,
        "absences": absences_result
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8880)