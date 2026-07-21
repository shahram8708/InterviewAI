"""
Analytics routes — feedback reports, interview history, progress, and achievements.
"""
from flask import Blueprint, render_template, flash, redirect, url_for, request
from app.utils.decorators import login_required
from app.utils.helpers import get_current_user
from app.models import InterviewSession, FeedbackReport, ProgressSnapshot, Badge, SkillGap
from app.services.scoring_service import calculate_streak

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/interview/session/<int:session_id>/report')
@login_required
def report(session_id):
    """Display the detailed feedback report for a completed interview session."""
    user = get_current_user()
    interview_session = InterviewSession.query.get_or_404(session_id)

    if interview_session.user_id != user.id:
        flash('You do not have access to this report.', 'error')
        return redirect(url_for('main.dashboard'))

    feedback = interview_session.feedback_report
    turns = interview_session.turns.order_by('sequence_number').all()

    return render_template('analytics/report.html',
                           session=interview_session,
                           report=feedback,
                           turns=turns)


@analytics_bp.route('/history')
@login_required
def history():
    """List all past interview sessions with optional filters."""
    user = get_current_user()

    # Optional filters
    company_filter = request.args.get('company', '')
    type_filter = request.args.get('type', '')
    status_filter = request.args.get('status', '')

    query = InterviewSession.query.filter_by(user_id=user.id)

    if company_filter:
        query = query.filter(InterviewSession.company_name.ilike(f'%{company_filter}%'))
    if type_filter:
        query = query.filter_by(interview_type=type_filter)
    if status_filter:
        query = query.filter_by(status=status_filter)

    sessions = query.order_by(InterviewSession.started_at.desc()).all()

    return render_template('analytics/history.html',
                           sessions=sessions,
                           company_filter=company_filter,
                           type_filter=type_filter,
                           status_filter=status_filter)


@analytics_bp.route('/progress')
@login_required
def progress():
    """Progress dashboard with trends, weekly reports, streaks, and skill gaps."""
    user = get_current_user()

    snapshots = ProgressSnapshot.query.filter_by(user_id=user.id)\
        .order_by(ProgressSnapshot.period_start_date.desc()).limit(12).all()
    snapshots.reverse()

    skill_gaps = SkillGap.query.filter_by(user_id=user.id)\
        .order_by(SkillGap.identified_at.desc()).limit(10).all()

    streak = calculate_streak(user.id)

    # Aggregate score data for chart
    completed = InterviewSession.query.filter_by(user_id=user.id, status='completed')\
        .order_by(InterviewSession.completed_at.desc()).limit(20).all()
    completed.reverse()

    score_data = []
    for s in completed:
        if s.feedback_report:
            score_data.append({
                'date': s.completed_at.strftime('%b %d') if s.completed_at else '',
                'score': s.feedback_report.overall_score,
                'company': s.company_name
            })

    return render_template('analytics/progress.html',
                           snapshots=snapshots,
                           skill_gaps=skill_gaps,
                           streak=streak,
                           score_data=score_data)


@analytics_bp.route('/achievements')
@login_required
def achievements():
    """Display the user's badge collection and progress toward next badges."""
    user = get_current_user()
    earned_badges = Badge.query.filter_by(user_id=user.id)\
        .order_by(Badge.earned_at.desc()).all()

    # Define all possible badges for the "unearned" display
    all_badge_types = {
        'first_interview': {'name': 'First Steps', 'desc': 'Complete your first interview', 'icon': '🎯'},
        'five_interviews': {'name': 'High Five', 'desc': 'Complete 5 interviews', 'icon': '🖐️'},
        'ten_interviews': {'name': 'Perfect Ten', 'desc': 'Complete 10 interviews', 'icon': '🔟'},
        'perfect_score': {'name': 'Perfectionist', 'desc': 'Score 95+ in an interview', 'icon': '⭐'},
        'streak_3': {'name': 'On Fire', 'desc': 'Practice 3 days in a row', 'icon': '🔥'},
        'streak_7': {'name': 'Unstoppable', 'desc': 'Practice 7 days in a row', 'icon': '🚀'},
        'speed_demon': {'name': 'Paced Perfectly', 'desc': 'Maintain ideal speaking speed', 'icon': '⏱️'},
        'smooth_talker': {'name': 'Smooth Talker', 'desc': 'Very few filler words used', 'icon': '🗣️'},
        'company_expert': {'name': 'Company Expert', 'desc': 'Complete 3+ interviews for one company', 'icon': '🏢'},
    }

    earned_types = {b.badge_type for b in earned_badges}

    return render_template('analytics/achievements.html',
                           earned_badges=earned_badges,
                           all_badge_types=all_badge_types,
                           earned_types=earned_types)
