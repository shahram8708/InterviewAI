"""
Route decorators — login_required and resume_required.
"""
from functools import wraps
from flask import session, redirect, url_for, flash
from app.models import ResumeProfile


def login_required(f):
    """Redirect to login if the user is not authenticated."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please sign in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def resume_required(f):
    """Redirect to resume upload if the user has no active resume."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if user_id:
            active_resume = ResumeProfile.query.filter_by(user_id=user_id, is_active=True).first()
            if not active_resume:
                flash('Please upload your resume before starting an interview.', 'warning')
                return redirect(url_for('resume.upload_get'))
        return f(*args, **kwargs)
    return decorated_function
