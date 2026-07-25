"""
Service for scoring and metrics calculation.
"""
from datetime import datetime, timezone, timedelta
import logging
from flask import current_app
from app.extensions import db
from app.models import FeedbackReport, ProgressSnapshot, Badge, SkillGap, InterviewSession
from app.services.gemini_service import generate_feedback_report
from app.services.voice_support import calculate_wpm
from app.services.badge_catalog import BADGE_DEFINITIONS
from app.services import analytics_service

logger = logging.getLogger(__name__)

def generate_scores(session: InterviewSession, turns: list, api_key: str) -> FeedbackReport:
    """Calculate all scores using Gemini rubric evaluation + objective signals, create and persist FeedbackReport."""
    ai_feedback = generate_feedback_report(api_key, session, turns)
    
    objective_metrics = calculate_objective_metrics(session)
    
    # Adjust scores based on objective metrics (simplified example)
    communication_score = ai_feedback.get('communication_score', 70)
    wpm = objective_metrics.get('average_wpm', 130)
    if wpm < 100 or wpm > 180:
        communication_score = max(0, communication_score - 10)
        
    report = FeedbackReport(
        session_id=session.id,
        overall_score=ai_feedback.get('overall_score', 70),
        communication_score=communication_score,
        technical_score=ai_feedback.get('technical_score', 70),
        confidence_score=ai_feedback.get('confidence_score', 70),
        problem_solving_score=ai_feedback.get('problem_solving_score', 70),
        leadership_score=ai_feedback.get('leadership_score', 70),
        behavioral_score=ai_feedback.get('behavioral_score', 70),
        strengths=ai_feedback.get('strengths', []),
        weaknesses=ai_feedback.get('weaknesses', []),
        missed_opportunities=ai_feedback.get('missed_opportunities', []),
        suggested_answers=ai_feedback.get('suggested_answers', {}),
        company_specific_recommendations=ai_feedback.get('company_specific_recommendations', []),
        improvement_plan=ai_feedback.get('improvement_plan', []),
        resume_suggestions=ai_feedback.get('resume_suggestions', []),
        communication_insights=ai_feedback.get('communication_insights', []),
        generated_at=datetime.now(timezone.utc)
    )
    
    db.session.add(report)
    db.session.commit()
    
    return report

def calculate_objective_metrics(session: InterviewSession) -> dict:
    """Compute filler-word rate and average WPM for a session."""
    turns = session.turns
    if not turns:
        return {'filler_rate': 0, 'average_wpm': 0}
        
    total_words = 0
    total_duration = 0.0
    total_fillers = 0
    
    for turn in turns:
        total_words += turn.word_count or 0
        total_duration += turn.speaking_duration_seconds or 0.0
        
        fillers = turn.filler_words_in_turn or {}
        total_fillers += sum(fillers.values())
        
    average_wpm = calculate_wpm(total_words, total_duration)
    filler_rate = (total_fillers / total_words) if total_words > 0 else 0
    
    return {
        'filler_rate': filler_rate,
        'average_wpm': average_wpm
    }

def detect_skill_gaps(user_id: int, session: InterviewSession, feedback_report: FeedbackReport) -> list:
    """Identify skill gaps from performance patterns, create SkillGap records."""
    new_gaps = []
    
    if feedback_report.technical_score < 60:
        gap = SkillGap(
            user_id=user_id,
            skill_name=f"Technical proficiency for {session.job_role}",
            severity="high",
            details="Scored below 60 on technical questions.",
            identified_at=datetime.now(timezone.utc),
            related_session_id=session.id
        )
        new_gaps.append(gap)
        
    if feedback_report.communication_score < 60:
        gap = SkillGap(
            user_id=user_id,
            skill_name="Verbal Communication",
            severity="medium",
            details="Communication score indicates room for improvement.",
            identified_at=datetime.now(timezone.utc),
            related_session_id=session.id
        )
        new_gaps.append(gap)
        
    if new_gaps:
        db.session.add_all(new_gaps)
        db.session.commit()
        
    return new_gaps

def check_and_award_badges(user_id: int) -> list:
    """Award any catalog badges whose conditions the user's real records now satisfy.

    Conditions live in ``badge_catalog`` and are evaluated against the same
    statistics the achievements page reads, so awarded badges and displayed
    achievements can never disagree. Already-earned badges are never duplicated.
    """
    statistics = analytics_service.get_user_statistics(user_id)
    existing_types = {
        badge_type for (badge_type,) in
        db.session.query(Badge.badge_type).filter(Badge.user_id == user_id).all()
    }

    new_badges = []
    for definition in BADGE_DEFINITIONS:
        if definition.badge_type in existing_types:
            continue
        if not definition.is_earned(statistics):
            continue
        new_badges.append(Badge(
            user_id=user_id,
            badge_type=definition.badge_type,
            badge_name=definition.name,
            badge_description=definition.description,
            badge_icon=definition.icon,
            earned_at=datetime.now(timezone.utc)
        ))

    if new_badges:
        db.session.add_all(new_badges)
        db.session.commit()

    return new_badges


def update_progress_snapshot(user_id: int):
    """Create or refresh the ProgressSnapshot for the current ISO week.

    ``period_start_date`` is a Date column, so the lookup must use a date value;
    comparing it against a datetime never matched and inserted a duplicate row on
    every call.
    """
    now = analytics_service.utc_now_naive()
    start_of_week_date = (now - timedelta(days=now.weekday())).date()
    start_of_week = datetime.combine(start_of_week_date, datetime.min.time())

    snapshot = ProgressSnapshot.query.filter_by(
        user_id=user_id,
        period_start_date=start_of_week_date
    ).first()

    if not snapshot:
        snapshot = ProgressSnapshot(
            user_id=user_id,
            period_start_date=start_of_week_date
        )
        db.session.add(snapshot)

    sessions_this_week = InterviewSession.query.filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == 'completed',
        InterviewSession.completed_at >= start_of_week
    ).all()

    total_score = 0.0
    valid_scores = 0
    total_wpm = 0
    valid_wpms = 0
    filler_totals = {}

    for s in sessions_this_week:
        if s.feedback_report:
            total_score += s.feedback_report.overall_score or 0
            valid_scores += 1

        metrics = calculate_objective_metrics(s)
        if metrics['average_wpm'] > 0:
            total_wpm += metrics['average_wpm']
            valid_wpms += 1

        for word, count in (s.filler_word_counts or {}).items():
            filler_totals[word] = filler_totals.get(word, 0) + count

    snapshot.sessions_completed = len(sessions_this_week)
    snapshot.streak_count = calculate_streak(user_id)
    snapshot.average_score = (total_score / valid_scores) if valid_scores else 0.0
    snapshot.average_speaking_speed_wpm = (total_wpm / valid_wpms) if valid_wpms else 0.0
    snapshot.filler_word_counts = filler_totals
    snapshot.generated_at = now

    db.session.commit()

def calculate_streak(user_id: int) -> int:
    """Return the user's current consecutive-day practice streak."""
    return analytics_service.calculate_current_streak(user_id)
