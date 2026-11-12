# ClassSense AI — Full-stack starter

A Flask + SQLite + HTML/CSS/JavaScript application for the Multimodal Attendance & Engagement Agent project.

## Included working features
- Responsive dashboard and navigation
- Student roster (add/list)
- Classroom session creation, listing and completion
- Manual attendance records with timestamps and duplicate protection
- Session-level indicator entry (0–100), trend chart and transparent rule-based teaching prompts
- Local upload storage for authorized MP4/MOV/AVI/WAV/MP3/M4A/PDF/CSV files
- SQLite database auto-created at startup
- Health endpoint at `/health`

## Run locally
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```
Open http://127.0.0.1:5000. A small sample roster is seeded on first run. Change or delete demo students before real use.

## Render deployment
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn run:app` (add `gunicorn` to requirements.txt for Render; or use `python run.py` for basic deployment)
- Set `HOST=0.0.0.0`, `PORT` is supplied by Render, and set a strong `SECRET_KEY`.
- SQLite and uploaded files on an ephemeral host filesystem can be lost on redeploy/restart. Use a persistent disk or managed PostgreSQL/object storage for production.
- For production, add authentication, role-based access, CSRF protection, rate limiting, secure cookies, backups, audit logs and HTTPS before exposing student information.

## Vercel deployment
- The app uses Vercel's temporary directory for its default SQLite database and uploads, avoiding writes to the read-only deployment bundle.
- Vercel temporary storage is not durable or shared across function instances. Configure durable external database and file storage before using the app for persistent data.

## Important scope / accuracy notes
This is a functioning application foundation, not a completed automated biometric attendance or emotion-recognition system.
- Attendance is manually confirmed by an educator. The app does not identify students from faces.
- Video/audio files are uploaded and stored locally, but no automatic media inference is run yet.
- Engagement indicators are educator-entered proxies. Rule-based prompts are generated from those entries; no model claims to know a learner's internal attention or understanding.
- The original diagram mentions hosted Google Gemini services. Hosted Gemini calls are not offline. This starter deliberately does not send student data to a cloud AI service. Add an AI provider only after deciding data governance, consent, retention and network requirements.
- For a true offline pipeline, add local video/audio feature extraction and validate it in your environment. Face detection alone cannot identify a person. Any identity matching requires explicit enrollment, consent, strong security, human review and legal/institutional approval.
