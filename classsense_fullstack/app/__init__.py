import os
from pathlib import Path
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from .extensions import db
from .routes import api

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///classsense.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH_MB", "250")) * 1024 * 1024
    upload_dir = Path(os.getenv("UPLOAD_FOLDER", "uploads"))
    if not upload_dir.is_absolute():
        upload_dir = Path(app.root_path).parent / upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = str(upload_dir)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    app.register_blueprint(api, url_prefix="/api")

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "ClassSense AI"})

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify({"error": "Upload exceeds the configured size limit."}), 413

    with app.app_context():
        from . import models  # noqa: F401
        db.create_all()
        _seed_demo_data()

    return app

def _seed_demo_data():
    from .models import Student
    if Student.query.count() == 0:
        db.session.add_all([
            Student(student_code="STU-001", full_name="Aarav Sharma", group_name="Class 10-A"),
            Student(student_code="STU-002", full_name="Diya Patel", group_name="Class 10-A"),
            Student(student_code="STU-003", full_name="Kabir Verma", group_name="Class 10-A"),
            Student(student_code="STU-004", full_name="Anaya Singh", group_name="Class 10-A"),
        ])
        db.session.commit()
