from flask import session
from app.models import User
from app.extensions import db

def get_current_user() -> User | None:
    user_id = session.get('user_id')
    if user_id:
        return db.session.get(User, user_id)
    return None

def format_duration(seconds: float) -> str:
    try:
        seconds = int(seconds)
        minutes = seconds // 60
        remaining = seconds % 60
        return f"{minutes:02d}:{remaining:02d}"
    except (ValueError, TypeError):
        return "00:00"

def format_date(dt) -> str:
    if not dt:
        return ""
    return dt.strftime("%B %d, %Y")

def get_score_color(score: float) -> str:
    if score >= 85:
        return "text-success"
    elif score >= 70:
        return "text-warning"
    return "text-danger"

def get_badge_info() -> dict:
    return {
        'first_interview': 'First Interview Completed',
        'perfect_score': 'Perfect Technical Score',
        'great_communicator': 'Great Communication',
        'problem_solver': 'Excellent Problem Solver',
        'streak_3': '3-Day Streak',
        'streak_7': '7-Day Streak'
    }
