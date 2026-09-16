from flask import Flask, jsonify, request
from uuid import uuid4
app3 = Flask(__name__)
STUDENTS = []
@app3.route("/students", methods=["POST"])
def create_student():
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    if not name:
        return jsonify({"error": "name la bat buoc"}), 400
    student = {
        "id": str(uuid4()),
        "name": name,
        "gpa": body.get("gpa", 0.0),
    }
    STUDENTS.append(student)
    return jsonify(student), 201
if __name__ == "__main__":
    app3.run(port=5000, debug=True)