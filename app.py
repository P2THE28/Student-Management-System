import json
from pathlib import Path
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

DATABASE = Path("data.json")


# ── helpers ──────────────────────────────────────────────────────────────────

def _load() -> list:
    if DATABASE.exists():
        try:
            return json.loads(DATABASE.read_text())
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save(data: list) -> None:
    DATABASE.write_text(json.dumps(data, indent=4))


def _find(data: list, grade: str, roll: str) -> dict | None:
    matches = [s for s in data if s["Roll_No"] == roll and s["Class"] == grade]
    return matches[0] if matches else None


def _err(msg: str, code: int = 400):
    return jsonify({"success": False, "message": msg}), code


def _ok(msg: str, **extra):
    return jsonify({"success": True, "message": msg, **extra})


# ── routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/students")
def list_students():
    return jsonify(_load())


@app.post("/api/students")
def add_student():
    body = request.json or {}
    required = ["Class", "Roll_No", "Name", "DOB", "Phone", "Father", "Mother", "Aadhar"]
    if missing := [f for f in required if not body.get(f, "").strip()]:
        return _err(f"Missing fields: {', '.join(missing)}")

    data = _load()
    if _find(data, body["Class"], body["Roll_No"]):
        return _err(f"Roll {body['Roll_No']} already exists in Class {body['Class']}")

    student = {k: body[k].strip() for k in required}
    data.append(student)
    _save(data)
    return _ok("Student added successfully", student=student), 201


@app.get("/api/students/<grade>/<roll>")
def get_student(grade, roll):
    student = _find(_load(), grade, roll)
    if not student:
        return _err("Student not found", 404)
    return jsonify(student)


@app.put("/api/students/<grade>/<roll>")
def update_student(grade, roll):
    body = request.json or {}
    data = _load()
    student = _find(data, grade, roll)
    if not student:
        return _err("Student not found", 404)

    new_class = body.get("Class", student["Class"]).strip() or student["Class"]
    try:
        if int(new_class) < int(student["Class"]):
            return _err("New class cannot be lower than current class")
    except ValueError:
        pass  # non-numeric class names are allowed

    updatable = ["Class", "Roll_No", "Name", "DOB", "Phone", "Father", "Mother", "Aadhar"]
    for key in updatable:
        val = body.get(key, "").strip()
        if val:
            student[key] = val

    _save(data)
    return _ok("Student updated successfully", student=student)


@app.delete("/api/students/<grade>/<roll>")
def delete_student(grade, roll):
    data = _load()
    student = _find(data, grade, roll)
    if not student:
        return _err("Student not found", 404)
    data.remove(student)
    _save(data)
    return _ok("Student deleted successfully")


if __name__ == "__main__":
    app.run(debug=True)
