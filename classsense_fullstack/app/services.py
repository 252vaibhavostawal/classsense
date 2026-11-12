from collections import defaultdict
from .models import Attendance, EngagementSignal, Student

def build_session_insights(session):
    signals = sorted(session.signals, key=lambda s: s.minute)
    by_minute = defaultdict(list)
    for signal in signals:
        by_minute[signal.minute].append(signal.value)
    timeline = [{"minute": minute, "score": round(sum(vals) / len(vals), 1)}
                for minute, vals in sorted(by_minute.items())]
    present = sum(1 for item in session.attendance if item.status == "present")
    total = Student.query.filter_by(active=True).count()
    average = round(sum(x["score"] for x in timeline) / len(timeline), 1) if timeline else None

    suggestions = []
    if timeline:
        scores = [x["score"] for x in timeline]
        if min(scores) < 40:
            suggestions.append("A low engagement indicator was recorded. Consider a short recap or a quick understanding check.")
        if len(scores) >= 3 and scores[-1] - scores[0] < -20:
            suggestions.append("The session trend declined over time. Consider adding a discussion or activity midway through the next session.")
        if max(scores) - min(scores) > 35:
            suggestions.append("The session showed substantial variation. Review the moments around the peaks and dips.")
    if not suggestions:
        suggestions.append("No strong pattern is available yet. Continue collecting session observations before drawing conclusions.")

    return {
        "attendance_present": present,
        "active_roster": total,
        "attendance_rate": round((present / total) * 100, 1) if total else 0,
        "average_signal": average,
        "timeline": timeline,
        "suggestions": suggestions,
        "interpretation_note": "Signals are indirect indicators, not a reliable measurement of attention, learning, effort or understanding. Educator review is required."
    }
