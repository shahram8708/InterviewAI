"""
Analytics routes — feedback reports, interview history, progress, and achievements.
"""
from flask import Blueprint, render_template, flash, redirect, url_for, request
from app.utils.decorators import login_required
from app.utils.helpers import get_current_user
from app.models import InterviewSession
from app.services import analytics_service

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

    # Calculate WPM
    wpm = 0
    if interview_session.total_speaking_time_seconds and interview_session.total_speaking_time_seconds > 0:
        wpm = int((interview_session.total_words_spoken or 0) / (interview_session.total_speaking_time_seconds / 60))

    # Construct qa_pairs
    qa_pairs = []
    for turn in turns:
        if turn.question_text:
            qa_pairs.append({
                'question': turn.question_text,
                'user_answer': turn.answer_text or 'No answer provided.',
                'feedback': turn.ai_notes or 'Average response.',
                'suggested_answer': turn.ai_response or 'N/A'
            })

    report_data = {
        'role': interview_session.job_role,
        'company': interview_session.company_name,
        'date': interview_session.started_at.strftime('%B %d, %Y') if interview_session.started_at else 'Unknown Date',
        'overall_score': int(feedback.overall_score) if feedback else 0,
        'categories': {
            'Communication': int(feedback.communication_score) if feedback else 0,
            'Technical': int(feedback.technical_score) if feedback else 0,
            'Confidence': int(feedback.confidence_score) if feedback else 0,
            'Problem Solving': int(feedback.problem_solving_score) if feedback else 0,
            'Leadership': int(feedback.leadership_score) if feedback else 0,
            'Behavioral': int(feedback.behavioral_score) if feedback else 0,
        },
        'strengths': feedback.strengths if feedback else [],
        'weaknesses': feedback.weaknesses if feedback else [],
        'improvement_plan': feedback.improvement_plan if feedback else [],
        'wpm': wpm,
        'filler_words': interview_session.filler_word_counts or {},
        'company_insights': feedback.company_specific_recommendations if feedback else [],
        'qa_pairs': qa_pairs
    }

    return render_template('analytics/report.html',
                           interview_session=interview_session,
                           report=report_data,
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
    """Progress dashboard — trends, weekly activity, streaks, and skill gaps."""
    user = get_current_user()

    statistics = analytics_service.get_user_statistics(user.id)

    return render_template('analytics/progress.html',
                           statistics=statistics,
                           category_averages=analytics_service.get_category_averages(user.id),
                           score_trend=analytics_service.get_score_trend(user.id),
                           weekly_activity=analytics_service.get_weekly_activity(user.id),
                           activity=analytics_service.get_recent_activity_comparison(user.id),
                           skill_gaps=analytics_service.get_skill_gap_summary(user.id, limit=10))


@analytics_bp.route('/achievements')
@login_required
def achievements():
    """Display achievements with unlock state and progress computed from real activity."""
    user = get_current_user()

    statistics = analytics_service.get_user_statistics(user.id)
    achievement_data = analytics_service.build_achievements(user.id, statistics)

    return render_template('analytics/achievements.html',
                           statistics=statistics,
                           **achievement_data)
