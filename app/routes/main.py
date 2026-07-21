"""
Main application routes — landing, dashboard, settings, about, security, offline.
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from app.utils.decorators import login_required
from app.utils.helpers import get_current_user
from app.extensions import db
from app.services.security_service import encrypt_api_key
from app.services.gemini_service import validate_api_key
from app.models import InterviewSession, ResumeProfile, ProgressSnapshot, Badge, SkillGap
from app.utils.validators import validate_api_key_format, validate_name, sanitize_input
from app.services.scoring_service import calculate_streak

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def landing():
    """Landing/marketing page. Redirect to dashboard if already logged in."""
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return render_template('main/landing.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main hub after login with recent sessions, streaks, badges, skill gaps."""
    user = get_current_user()
    recent_sessions = InterviewSession.query.filter_by(user_id=user.id)\
        .order_by(InterviewSession.started_at.desc()).limit(5).all()
    active_resume = ResumeProfile.query.filter_by(user_id=user.id, is_active=True).first()
    badges = Badge.query.filter_by(user_id=user.id).order_by(Badge.earned_at.desc()).limit(5).all()
    skill_gaps = SkillGap.query.filter_by(user_id=user.id).order_by(SkillGap.identified_at.desc()).limit(5).all()
    streak = calculate_streak(user.id)

    completed_sessions = InterviewSession.query.filter_by(user_id=user.id, status='completed').all()
    scores = []
    for s in completed_sessions:
        if s.feedback_report:
            scores.append({
                'date': s.completed_at.strftime('%b %d') if s.completed_at else '',
                'score': s.feedback_report.overall_score
            })

    return render_template('main/dashboard.html',
                           user=user,
                           recent_sessions=recent_sessions,
                           active_resume=active_resume,
                           badges=badges,
                           skill_gaps=skill_gaps,
                           streak=streak,
                           scores=scores,
                           total_sessions=len(completed_sessions))


@main_bp.route('/about')
def about():
    """About page with conditional institutional branding."""
    return render_template('main/about.html')


@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Profile management — update name, preferences, rotate API key."""
    user = get_current_user()

    if request.method == 'POST':
        action = request.form.get('action', '')

        if action == 'update_profile':
            new_name = sanitize_input(request.form.get('full_name', '').strip())
            is_valid, err = validate_name(new_name)
            if is_valid:
                user.full_name = new_name
                session['user_name'] = new_name
                db.session.commit()
                flash('Profile updated successfully.', 'success')
            else:
                flash(err, 'error')

        elif action == 'update_prefs':
            user.theme_preference = request.form.get('theme', 'system')
            user.high_contrast = request.form.get('high_contrast') == 'on'
            user.reduced_motion = request.form.get('reduced_motion') == 'on'
            user.speech_locale = request.form.get('speech_locale', 'en-US')
            try:
                user.voice_speed = float(request.form.get('voice_speed', '1.0'))
            except (ValueError, TypeError):
                user.voice_speed = 1.0
            db.session.commit()
            flash('Preferences updated successfully.', 'success')

        elif action == 'rotate_key':
            new_key = request.form.get('api_key', '').strip()
            is_valid_key, key_err = validate_api_key_format(new_key)
            if not is_valid_key:
                flash(key_err, 'error')
            else:
                try:
                    if not validate_api_key(new_key):
                        flash('Invalid API key. Please check and try again.', 'error')
                    else:
                        user.encrypted_api_key = encrypt_api_key(new_key)
                        db.session.commit()
                        flash('API key updated successfully.', 'success')
                except Exception:
                    flash('Unable to verify the new API key. Please try again.', 'error')

        return redirect(url_for('main.settings'))

    return render_template('main/settings.html', user=user)


@main_bp.route('/security')
def security():
    """Security & Privacy explanation page."""
    return render_template('main/security.html')


@main_bp.route('/offline')
def offline():
    """PWA offline fallback page."""
    return render_template('main/offline.html')
