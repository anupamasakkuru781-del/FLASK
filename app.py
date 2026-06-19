from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

db = mysql.connector.connect(
    host="localhost",
    user="root",        
    password="root",
    database="student_db"
)

cursor = db.cursor(dictionary=True)

@app.route('/')
def Home():
    return jsonify({"message": "Welcome to the Student Management System API!"})

@app.route('/students', methods=['GET'])
def Students():
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    return jsonify(students)

@app.route('/students', methods=['POST'])
def add_student():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    course = data.get('course')
    phone = data.get('phone')

    query = "INSERT INTO students ( name, email, course, phone) VALUES (%s, %s, %s, %s)"
    values = ( name, email, course, phone)

    cursor.execute(query, values)
    db.commit()
    return jsonify({"message": "Student added successfully!"}) 

@app.route('/update/<int:id>', methods=['PUT'])
def update_student(id):
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    course = data.get('course')
    phone = data.get('phone')

    sql = "UPDATE students SET name = %s, email = %s, course = %s, phone = %s WHERE id = %s"
    value = (name, email, course, phone, id)

    cursor.execute(sql, value)
    db.commit()

    return jsonify({"message": "Student updated successfully"})

@app.route('/delete/<int:id>', methods=['DELETE'])
def delete_student(id):
    sql = "DELETE FROM students WHERE id = %s"
    value = (id,)

    cursor.execute(sql, value)
    db.commit()

    return jsonify({"message": "Student deleted successfully"})


if __name__ == '__main__':
    app.run(debug=True)






