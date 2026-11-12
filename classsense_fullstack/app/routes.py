import os
from datetime import datetime, timezone
from pathlib import Path
from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename
from .extensions import db
from .models import Student, Session, Attendance, EngagementSignal, Upload
from .services import build_session_insights

api = Blueprint("api", __name__)

def error(message, status=400):
    return jsonify({"error": message}), status

def session_or_404(session_id):
    item = db.session.get(Session, session_id)
    return item

@api.get("/dashboard")
def dashboard():
    sessions = Session.query.order_by(Session.started_at.desc()).limit(8).all()
    active = Session.query.filter_by(status="active").count()
    students = Student.query.filter_by(active=True).count()
    recent = []
    for s in sessions:
        recent.append({
            "id": s.id, "title": s.title, "class_name": s.class_name,
            "status": s.status, "started_at": s.started_at.isoformat(),
            "present": sum(1 for a in s.attendance if a.status == "present")
        })
    return jsonify({"active_sessions": active, "active_students": students,
                    "total_sessions": Session.query.count(), "recent_sessions": recent})

@api.get("/students")
def list_students():
    items = Student.query.order_by(Student.full_name).all()
    return jsonify([{"id": s.id, "student_code": s.student_code, "full_name": s.full_name,
                     "group_name": s.group_name, "active": s.active} for s in items])

@api.post("/students")
def add_student():
    data = request.get_json(silent=True) or {}
    code, name = (data.get("student_code") or "").strip(), (data.get("full_name") or "").strip()
    if not code or not name:
        return error("student_code and full_name are required.")
    if Student.query.filter_by(student_code=code).first():
        return error("That student code already exists.")
    student = Student(student_code=code, full_name=name,
                      group_name=(data.get("group_name") or "Unassigned").strip())
    db.session.add(student)
    db.session.commit()
    return jsonify({"id": student.id, "message": "Student added."}), 201

@api.post("/sessions")
def create_session():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return error("Session title is required.")
    item = Session(title=title, class_name=(data.get("class_name") or "General").strip(),
                   notes=(data.get("notes") or "").strip())
    db.session.add(item)
    db.session.commit()
    return jsonify({"id": item.id, "message": "Session created.", "status": item.status}), 201

@api.get("/sessions")
def list_sessions():
    items = Session.query.order_by(Session.started_at.desc()).all()
    return jsonify([{"id": s.id, "title": s.title, "class_name": s.class_name,
                     "status": s.status, "started_at": s.started_at.isoformat(),
                     "ended_at": s.ended_at.isoformat() if s.ended_at else None,
                     "present": sum(1 for a in s.attendance if a.status == "present")}
                    for s in items])

@api.post("/sessions/<int:session_id>/end")
def end_session(session_id):
    item = session_or_404(session_id)
    if not item:
        return error("Session not found.", 404)
    item.status = "completed"
    item.ended_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({"message": "Session completed."})

@api.post("/sessions/<int:session_id>/attendance")
def mark_attendance(session_id):
    item = session_or_404(session_id)
    if not item:
        return error("Session not found.", 404)
    data = request.get_json(silent=True) or {}
    student_id = data.get("student_id")
    student = db.session.get(Student, student_id) if student_id else None
    if not student or not student.active:
        return error("Select an active student.")
    record = Attendance.query.filter_by(session_id=session_id, student_id=student.id).first()
    if record:
        record.status = data.get("status", "present")
        record.marked_at = datetime.now(timezone.utc)
    else:
        record = Attendance(session_id=session_id, student_id=student.id,
                            status=data.get("status", "present"), method="manual")
        db.session.add(record)
    db.session.commit()
    return jsonify({"message": "Attendance saved.", "student": student.full_name})

@api.get("/sessions/<int:session_id>/attendance")
def session_attendance(session_id):
    item = session_or_404(session_id)
    if not item:
        return error("Session not found.", 404)
    rows = Attendance.query.filter_by(session_id=session_id).all()
    return jsonify([{"student_id": a.student_id, "student_code": a.student.student_code,
                     "full_name": a.student.full_name, "status": a.status,
                     "marked_at": a.marked_at.isoformat(), "method": a.method} for a in rows])

@api.post("/sessions/<int:session_id>/signals")
def add_signal(session_id):
    item = session_or_404(session_id)
    if not item:
        return error("Session not found.", 404)
    data = request.get_json(silent=True) or {}
    try:
        minute = int(data.get("minute"))
        value = float(data.get("value"))
    except (TypeError, ValueError):
        return error("minute must be an integer and value must be numeric.")
    signal_type = (data.get("signal_type") or "engagement_proxy").strip()
    if minute < 0 or not 0 <= value <= 100:
        return error("minute must be >= 0 and value must be between 0 and 100.")
    signal = EngagementSignal(session_id=session_id, minute=minute, value=value,
                              signal_type=signal_type, source="educator_entered")
    db.session.add(signal)
    db.session.commit()
    return jsonify({"message": "Signal saved."}), 201

@api.get("/sessions/<int:session_id>/insights")
def session_insights(session_id):
    item = session_or_404(session_id)
    if not item:
        return error("Session not found.", 404)
    return jsonify(build_session_insights(item))

@api.post("/sessions/<int:session_id>/uploads")
def upload_file(session_id):
    item = session_or_404(session_id)
    if not item:
        return error("Session not found.", 404)
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return error("Choose a file to upload.")
    safe = secure_filename(uploaded.filename)
    if not safe:
        return error("Invalid filename.")
    allowed = {".mp4", ".mov", ".avi", ".wav", ".mp3", ".m4a", ".pdf", ".csv"}
    ext = Path(safe).suffix.lower()
    if ext not in allowed:
        return error("Supported formats: MP4, MOV, AVI, WAV, MP3, M4A, PDF and CSV.")
    stored = f"{session_id}_{int(datetime.now(timezone.utc).timestamp())}_{safe}"
    destination = Path(current_app.config["UPLOAD_FOLDER"]) / stored
    uploaded.save(destination)
    record = Upload(session_id=session_id, original_name=safe, stored_name=stored,
                    media_type=uploaded.mimetype or "application/octet-stream")
    db.session.add(record)
    db.session.commit()
    return jsonify({"message": "File uploaded and stored locally.", "filename": safe}), 201
