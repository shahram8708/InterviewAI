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
    """Compute filler word rate, WPM, answer length consistency."""
    turns = session.turns
    if not turns:
        return {'filler_rate': 0, 'average_wpm': 0, 'length_consistency': 0}
        
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
        'average_wpm': average_wpm,
        'length_consistency': 1.0 # placeholder
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
    """Check badge criteria and award new badges."""
    # Assuming user has sessions
    sessions = InterviewSession.query.filter_by(user_id=user_id, status='completed').all()
    count = len(sessions)
    
    existing_badges = [b.badge_type for b in Badge.query.filter_by(user_id=user_id).all()]
    new_badges = []
    
    def award(badge_type, name, desc, icon):
        if badge_type not in existing_badges:
            badge = Badge(
                user_id=user_id,
                badge_type=badge_type,
                badge_name=name,
                badge_description=desc,
                badge_icon=icon,
                earned_at=datetime.now(timezone.utc)
            )
            new_badges.append(badge)
            existing_badges.append(badge_type)
            
    if count >= 1:
        award('first_interview', 'First Steps', 'Completed your first interview.', '🎯')
    if count >= 5:
        award('five_interviews', 'High Five', 'Completed 5 interviews.', '🖐️')
    if count >= 10:
        award('ten_interviews', 'Perfect Ten', 'Completed 10 interviews.', '🔟')
        
    streak = calculate_streak(user_id)
    if streak >= 3:
        award('streak_3', 'On Fire', 'Completed interviews 3 days in a row.', '🔥')
    if streak >= 7:
        award('streak_7', 'Unstoppable', 'Completed interviews 7 days in a row.', '🚀')
        
    # Checking perfect score
    has_perfect = False
    has_fast = False
    has_smooth = False
    company_counts = {}
    
    for s in sessions:
        if s.feedback_report and s.feedback_report.overall_score >= 95:
            has_perfect = True
        
        metrics = calculate_objective_metrics(s)
        if 140 <= metrics['average_wpm'] <= 160:
            has_fast = True
        if metrics['filler_rate'] < 0.01:
            has_smooth = True
            
        company_counts[s.company_name] = company_counts.get(s.company_name, 0) + 1
        
    if has_perfect:
        award('perfect_score', 'Perfectionist', 'Scored 95+ in an interview.', '⭐')
    if has_fast:
        award('speed_demon', 'Paced Perfectly', 'Maintained ideal speaking speed.', '⏱️')
    if has_smooth:
        award('smooth_talker', 'Smooth Talker', 'Very few filler words used.', '🗣️')
        
    for comp, c in company_counts.items():
        if c >= 3 and comp and comp.lower() not in ['none', 'n/a', 'unknown']:
            award('company_expert', 'Company Expert', f'Completed 3+ interviews for a single company.', '🏢')
            
    if new_badges:
        db.session.add_all(new_badges)
        db.session.commit()
        
    return new_badges

def update_progress_snapshot(user_id: int):
    """Create/update weekly ProgressSnapshot."""
    now = datetime.now(timezone.utc)
    start_of_week = now - timedelta(days=now.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    
    snapshot = ProgressSnapshot.query.filter_by(
        user_id=user_id,
        period_start_date=start_of_week
    ).first()
    
    if not snapshot:
        snapshot = ProgressSnapshot(
            user_id=user_id,
            period_start_date=start_of_week,
            sessions_completed=0,
            average_score=0.0,
            streak_count=calculate_streak(user_id),
            filler_word_counts={},
            average_speaking_speed_wpm=0.0,
            generated_at=now
        )
        db.session.add(snapshot)
        
    sessions_this_week = InterviewSession.query.filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == 'completed',
        InterviewSession.completed_at >= start_of_week
    ).all()
    
    snapshot.sessions_completed = len(sessions_this_week)
    snapshot.streak_count = calculate_streak(user_id)
    
    if sessions_this_week:
        total_score = 0
        total_wpm = 0
        valid_scores = 0
        valid_wpms = 0
        
        for s in sessions_this_week:
            if s.feedback_report:
                total_score += s.feedback_report.overall_score
                valid_scores += 1
            
            metrics = calculate_objective_metrics(s)
            if metrics['average_wpm'] > 0:
                total_wpm += metrics['average_wpm']
                valid_wpms += 1
                
        if valid_scores > 0:
            snapshot.average_score = total_score / valid_scores
        if valid_wpms > 0:
            snapshot.average_speaking_speed_wpm = total_wpm / valid_wpms
            
    snapshot.generated_at = now
    db.session.commit()

def calculate_streak(user_id: int) -> int:
    """Calculate consecutive days with interviews."""
    sessions = InterviewSession.query.filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == 'completed',
        InterviewSession.completed_at != None
    ).order_by(InterviewSession.completed_at.desc()).all()
    
    if not sessions:
        return 0
        
    unique_dates = []
    for s in sessions:
        d = s.completed_at.date()
        if d not in unique_dates:
            unique_dates.append(d)
            
    today = datetime.now(timezone.utc).date()
    streak = 0
    
    if unique_dates and unique_dates[0] < today - timedelta(days=1):
        return 0
        
    current_date = unique_dates[0] if unique_dates and unique_dates[0] == today else today - timedelta(days=1)
    
    if unique_dates and unique_dates[0] == today:
        streak = 1
        idx = 1
    else:
        streak = 0
        idx = 0
        
    while idx < len(unique_dates):
        if unique_dates[idx] == current_date - timedelta(days=1):
            streak += 1
            current_date = unique_dates[idx]
            idx += 1
        else:
            break
            
    return streak
