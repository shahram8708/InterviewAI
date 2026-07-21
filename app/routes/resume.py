"""
Resume upload and profile routes.
"""
import json
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from app.utils.decorators import login_required
from app.utils.helpers import get_current_user
from app.extensions import db, limiter
from app.services.resume_service import process_resume, validate_pdf
from app.models import ResumeProfile
from app.services.security_service import decrypt_api_key

resume_bp = Blueprint('resume', __name__, url_prefix='/resume')


@resume_bp.route('/upload', methods=['GET'])
@login_required
def upload_get():
    """Show the resume upload form."""
    user = get_current_user()
    active_resume = ResumeProfile.query.filter_by(user_id=user.id, is_active=True).first()
    return render_template('resume/upload.html',
                           active_resume=active_resume,
                           max_size=current_app.config.get('MAX_UPLOAD_SIZE_MB', 10))


@resume_bp.route('/upload', methods=['POST'])
@login_required
@limiter.limit(lambda: current_app.config.get('RATE_LIMIT_RESUME', '10/day'))
def upload_post():
    """Process the uploaded PDF resume through the full analysis pipeline."""
    if 'resume' not in request.files:
        flash('No file selected. Please choose a PDF file.', 'error')
        return redirect(url_for('resume.upload_get'))

    file = request.files['resume']
    if not file.filename or file.filename == '':
        flash('No file selected. Please choose a PDF file.', 'error')
        return redirect(url_for('resume.upload_get'))

    is_valid, validation_msg = validate_pdf(file)
    if not is_valid:
        flash(validation_msg, 'error')
        return redirect(url_for('resume.upload_get'))

    try:
        user = get_current_user()
        api_key = decrypt_api_key(user.encrypted_api_key)

        # Deactivate any existing active resume
        ResumeProfile.query.filter_by(user_id=user.id, is_active=True)\
            .update({'is_active': False})
        db.session.flush()

        profile = process_resume(file, user.id, api_key)

        if profile:
            flash('Resume analyzed successfully! Review your profile below.', 'success')
            return redirect(url_for('resume.profile'))
        else:
            flash('Failed to process your resume. Please try again.', 'error')
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        current_app.logger.error(f'Resume processing error: {e}')
        flash('An unexpected error occurred while processing your resume. Please try again.', 'error')

    return redirect(url_for('resume.upload_get'))


@resume_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    """Display the extracted structured resume profile for review."""
    user = get_current_user()
    active_resume = ResumeProfile.query.filter_by(user_id=user.id, is_active=True).first()

    if not active_resume:
        flash('Please upload a resume first.', 'warning')
        return redirect(url_for('resume.upload_get'))

    return render_template('resume/profile.html', profile=active_resume)


@resume_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update individual profile fields from the review/edit form."""
    user = get_current_user()
    active_resume = ResumeProfile.query.filter_by(user_id=user.id, is_active=True).first()

    if not active_resume:
        flash('No active resume found.', 'error')
        return redirect(url_for('resume.upload_get'))

    try:
        if request.form.get('skills'):
            active_resume.skills = [s.strip() for s in request.form.get('skills', '').split(',') if s.strip()]
        if request.form.get('technologies'):
            active_resume.technologies = [t.strip() for t in request.form.get('technologies', '').split(',') if t.strip()]
        if request.form.get('strengths'):
            active_resume.strengths = [s.strip() for s in request.form.get('strengths', '').split(',') if s.strip()]
        if request.form.get('career_level'):
            active_resume.career_level = request.form.get('career_level', '').strip()
        if request.form.get('summary'):
            active_resume.summary = request.form.get('summary', '').strip()

        db.session.commit()
        flash('Profile updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Profile update error: {e}')
        flash('Failed to update profile. Please try again.', 'error')

    return redirect(url_for('resume.profile'))
