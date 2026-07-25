"""
Interview configuration, session creation, and live interview room routes.
"""
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from app.utils.decorators import login_required, resume_required
from app.utils.helpers import get_current_user
from app.extensions import db
from app.models import InterviewSession, ResumeProfile
from app.services.context_service import build_initial_context
from app.services.research_service import research_company
from app.services.security_service import decrypt_api_key
from app.utils.validators import validate_job_role, validate_company_name, sanitize_input
import json

interview_bp = Blueprint('interview', __name__, url_prefix='/interview')

EXPERIENCE_LEVELS = ['Fresher', '1-2 Years', '3-5 Years', '5+ Years']
INTERVIEW_TYPES = ['HR Interview', 'Technical Interview', 'Behavioral Interview',
                   'System Design Interview', 'Mixed Round']
PERSONAS = {
    'friendly': {'name': 'Friendly Recruiter', 'desc': 'Encouraging and supportive, warm vocal tone'},
    'strict': {'name': 'Strict Hiring Manager', 'desc': 'Professional and challenging, formal tone'},
    'technical': {'name': 'Senior Technical Lead', 'desc': 'Deep probing technical questions, confident tone'},
    'faang': {'name': 'FAANG Interviewer', 'desc': 'High-standard rigorous simulation, analytical tone'}
}


@interview_bp.route('/configure', methods=['GET'])
@login_required
@resume_required
def configure_get():
    """Show the interview configuration form with presets."""
    return render_template('interview/configure.html',
                           experience_levels=EXPERIENCE_LEVELS,
                           interview_types=INTERVIEW_TYPES,
                           personas=PERSONAS)


@interview_bp.route('/configure', methods=['POST'])
@login_required
@resume_required
def configure_post():
    """Validate interview configuration and show confirmation screen."""
    job_role = sanitize_input(request.form.get('job_role', '').strip())
    custom_role = sanitize_input(request.form.get('custom_job_role', '').strip())
    company_name = sanitize_input(request.form.get('company_name', '').strip())
    custom_company = sanitize_input(request.form.get('custom_company', '').strip())
    experience_level = request.form.get('experience_level', 'Fresher')
    interview_type = request.form.get('interview_type', 'Mixed Round')
    interviewer_persona = request.form.get('interviewer_persona', 'friendly')

    # Use custom values if "Other" was selected
    if job_role == 'Other' and custom_role:
        job_role = custom_role
    if company_name == 'Other' and custom_company:
        company_name = custom_company

    valid_role, role_err = validate_job_role(job_role)
    if not valid_role:
        flash(role_err, 'error')
        return redirect(url_for('interview.configure_get'))

    valid_comp, comp_err = validate_company_name(company_name)
    if not valid_comp:
        flash(comp_err, 'error')
        return redirect(url_for('interview.configure_get'))

    if experience_level not in EXPERIENCE_LEVELS:
        flash('Please select a valid experience level.', 'error')
        return redirect(url_for('interview.configure_get'))

    if interview_type not in INTERVIEW_TYPES:
        flash('Please select a valid interview type.', 'error')
        return redirect(url_for('interview.configure_get'))

    if interviewer_persona not in PERSONAS:
        interviewer_persona = 'friendly'

    persona_info = PERSONAS.get(interviewer_persona, PERSONAS['friendly'])

    return render_template('interview/confirm.html',
                           job_role=job_role,
                           company_name=company_name,
                           experience_level=experience_level,
                           interview_type=interview_type,
                           interviewer_persona=interviewer_persona,
                           persona_name=persona_info['name'])


@interview_bp.route('/start', methods=['POST'])
@login_required
@resume_required
def start():
    """Create the InterviewSession, trigger research, build context, redirect to live room."""
    user = get_current_user()
    job_role = sanitize_input(request.form.get('job_role', '').strip())
    company_name = sanitize_input(request.form.get('company_name', '').strip())
    experience_level = request.form.get('experience_level', 'Fresher')
    interview_type = request.form.get('interview_type', 'Mixed Round')
    interviewer_persona = request.form.get('interviewer_persona', 'friendly')

    active_resume = ResumeProfile.query.filter_by(user_id=user.id, is_active=True).first()
    if not active_resume:
        flash('Please upload a resume first.', 'warning')
        return redirect(url_for('resume.upload_get'))

    try:
        api_key = decrypt_api_key(user.encrypted_api_key)

        # Research company with Google Search grounding
        company_data = {}
        try:
            company_data = research_company(api_key, company_name, job_role, experience_level)
        except Exception as e:
            current_app.logger.warning(f'Company research failed, continuing without: {e}')

        # Create session record
        interview_session = InterviewSession(
            user_id=user.id,
            resume_profile_id=active_resume.id,
            job_role=job_role,
            company_name=company_name,
            experience_level=experience_level,
            interview_type=interview_type,
            interviewer_persona=interviewer_persona,
            status='in_progress',
            company_research=company_data,
            total_questions_target=10,
            current_stage='introduction'
        )
        db.session.add(interview_session)
        db.session.flush()

        # Build initial compressed context
        initial_context = build_initial_context(active_resume, interview_session)
        # Merge in company research summary
        if company_data:
            initial_context['company_research'] = {
                'culture': company_data.get('culture_notes', ''),
                'interview_patterns': company_data.get('interview_patterns', []),
                'common_questions': company_data.get('common_questions', []),
                'role_expectations': company_data.get('role_expectations', '')
            }
        interview_session.compressed_context = initial_context
        db.session.commit()

        flash('Interview session started! Good luck!', 'success')
        return redirect(url_for('interview.session_view', session_id=interview_session.id))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Failed to start interview: {e}')
        flash('Failed to start the interview session. Please try again.', 'error')
        return redirect(url_for('interview.configure_get'))


@interview_bp.route('/session/<int:session_id>', methods=['GET'])
@login_required
def session_view(session_id):
    """Render the live interview room."""
    user = get_current_user()
    interview_session = InterviewSession.query.get_or_404(session_id)

    if interview_session.user_id != user.id:
        flash('You do not have access to this interview session.', 'error')
        return redirect(url_for('main.dashboard'))

    if interview_session.status == 'completed':
        return redirect(url_for('analytics.report', session_id=session_id))

    persona_info = PERSONAS.get(interview_session.interviewer_persona, PERSONAS['friendly'])

    session_data = json.dumps({
        'id': interview_session.id,
        'persona': interview_session.interviewer_persona,
        'total_questions': getattr(interview_session, 'total_questions_target', 5)
    })

    return render_template('interview/session.html',
                           interview_session=interview_session,
                           session_data=session_data,
                           persona=persona_info,
                           user=user)
