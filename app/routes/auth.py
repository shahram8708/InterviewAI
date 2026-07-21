"""
Authentication routes — login, logout, and API key onboarding guide.
"""
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from app.extensions import db, limiter
from app.models import User
from app.services.security_service import encrypt_api_key
from app.services.gemini_service import validate_api_key
from app.utils.validators import validate_name, validate_api_key_format, sanitize_input

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit(lambda: current_app.config.get('RATE_LIMIT_LOGIN', '10/hour'))
def login():
    """Handle user login with name + Gemini API key."""
    if request.method == 'POST':
        full_name = sanitize_input(request.form.get('full_name', '').strip())
        api_key = request.form.get('api_key', '').strip()

        is_valid_name, name_err = validate_name(full_name)
        if not is_valid_name:
            flash(name_err, 'error')
            return render_template('auth/login.html'), 400

        is_valid_key, key_err = validate_api_key_format(api_key)
        if not is_valid_key:
            flash(key_err, 'error')
            return render_template('auth/login.html'), 400

        try:
            if not validate_api_key(api_key):
                flash('Invalid API key. Please check your Gemini API key and try again.', 'error')
                return render_template('auth/login.html'), 401
        except Exception:
            flash('Unable to verify your API key. Please check your internet connection and try again.', 'error')
            return render_template('auth/login.html'), 503

        encrypted_key = encrypt_api_key(api_key)

        user = User.query.filter_by(full_name=full_name).first()
        if user:
            user.encrypted_api_key = encrypted_key
            user.last_login_at = datetime.now(timezone.utc)
        else:
            user = User(
                full_name=full_name,
                encrypted_api_key=encrypted_key,
                last_login_at=datetime.now(timezone.utc)
            )
            db.session.add(user)

        db.session.commit()

        # Regenerate session to prevent session fixation
        session.clear()
        session['user_id'] = user.id
        session['user_name'] = user.full_name
        session.permanent = True

        flash('Welcome! You are now signed in.', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    """Clear the server-side session and redirect to landing."""
    session.clear()
    flash('You have been signed out.', 'info')
    return redirect(url_for('main.landing'))


@auth_bp.route('/onboarding/api-key-guide')
def api_key_guide():
    """Render the step-by-step Gemini API key walkthrough."""
    return render_template('auth/api_key_guide.html')
