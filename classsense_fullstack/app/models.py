from datetime import datetime, timezone
from .extensions import db

def utcnow():
    return datetime.now(timezone.utc)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_code = db.Column(db.String(40), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    group_name = db.Column(db.String(80), default="Unassigned")
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    class_name = db.Column(db.String(100), default="General")
    started_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    ended_at = db.Column(db.DateTime(timezone=True), nullable=True)
    status = db.Column(db.String(20), default="active", nullable=False)
    notes = db.Column(db.Text, default="")
    attendance = db.relationship("Attendance", backref="session", cascade="all, delete-orphan")
    signals = db.relationship("EngagementSignal", backref="session", cascade="all, delete-orphan")

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("session.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    marked_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    method = db.Column(db.String(30), default="manual")
    status = db.Column(db.String(20), default="present")
    student = db.relationship("Student")
    __table_args__ = (db.UniqueConstraint("session_id", "student_id", name="unique_session_student"),)

class EngagementSignal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("session.id"), nullable=False)
    minute = db.Column(db.Integer, nullable=False)
    signal_type = db.Column(db.String(40), nullable=False)
    value = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(40), default="manual_or_imported")
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("session.id"), nullable=True)
    original_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False)
    media_type = db.Column(db.String(80), nullable=False)
    uploaded_at = db.Column(db.DateTime(timezone=True), default=utcnow)
