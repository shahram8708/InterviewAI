"""
Analytics service — derives every dashboard, progress, and achievement metric
from the authenticated user's own database records.

All queries are scoped by ``user_id`` and aggregate in the database wherever the
storage engine allows it. The only values loaded into Python are the JSON
filler-word maps, which no supported backend can aggregate portably.

Every function in this module returns real measurements. When a user has no
records the functions return zeros, empty lists, or ``None`` so the templates can
render an honest empty state instead of an invented one.
"""
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import case, func
from sqlalchemy.orm import load_only

from app.extensions import db
from app.models import (Badge, FeedbackReport, InterviewSession, ResumeProfile,
                        SkillGap)
from app.services.badge_catalog import (BADGE_DEFINITIONS, IDEAL_WPM_RANGE,
                                        MIN_WORDS_FOR_FLUENCY_BADGE,
                                        TOTAL_BADGE_COUNT)

logger = logging.getLogger(__name__)

SESSION_STATUS_COMPLETED = 'completed'
SESSION_STATUS_IN_PROGRESS = 'in_progress'

# Number of most recent completed interviews plotted on the score-trend chart.
SCORE_TREND_LIMIT = 20

# Rolling window used for the weekly activity comparison on the progress page.
ACTIVITY_WINDOW_DAYS = 7

# Human-readable labels for the per-category score columns on FeedbackReport.
SCORE_CATEGORIES = (
    ('communication_score', 'Communication'),
    ('technical_score', 'Technical'),
    ('confidence_score', 'Confidence'),
    ('problem_solving_score', 'Problem Solving'),
    ('leadership_score', 'Leadership'),
    ('behavioral_score', 'Behavioural'),
)

SEVERITY_ORDER = {'high': 0, 'medium': 1, 'low': 2}


def utc_now_naive() -> datetime:
    """Return the current UTC time as a naive datetime.

    Model defaults store ``datetime.now(timezone.utc)``, which SQLite persists
    without a timezone. Comparisons must therefore use naive UTC values so that
    filters behave identically across backends.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _completed_sessions_query(user_id: int):
    """Base query for a user's completed interviews that have a completion timestamp."""
    return InterviewSession.query.filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == SESSION_STATUS_COMPLETED,
        InterviewSession.completed_at.isnot(None),
    )


def _as_date(value) -> date | None:
    """Normalise a database date expression to a ``date`` across backends."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def get_completed_session_dates(user_id: int) -> list[date]:
    """Return the distinct UTC dates on which the user completed an interview, newest first."""
    rows = db.session.query(
        func.date(InterviewSession.completed_at).label('day')
    ).filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == SESSION_STATUS_COMPLETED,
        InterviewSession.completed_at.isnot(None),
    ).distinct().all()

    days = [_as_date(row.day) for row in rows]
    return sorted({day for day in days if day is not None}, reverse=True)


def calculate_current_streak(user_id: int) -> int:
    """Count consecutive practice days ending today or yesterday.

    Yesterday still counts so that a streak is not reported as broken partway
    through the current day. Any older gap ends the streak.
    """
    return calculate_current_streak_from_dates(get_completed_session_dates(user_id))


def calculate_current_streak_from_dates(practice_days: list[date]) -> int:
    """Compute the current streak from an already-loaded, descending list of dates."""
    if not practice_days:
        return 0

    today = utc_now_naive().date()
    most_recent = practice_days[0]

    if most_recent < today - timedelta(days=1):
        return 0

    streak = 1
    expected = most_recent - timedelta(days=1)
    for day in practice_days[1:]:
        if day != expected:
            break
        streak += 1
        expected = day - timedelta(days=1)

    return streak


def calculate_longest_streak_from_dates(practice_days: list[date]) -> int:
    """Compute the longest run of consecutive practice days the user has ever achieved."""
    if not practice_days:
        return 0

    longest = 1
    current = 1
    for previous, day in zip(practice_days, practice_days[1:]):
        if previous - day == timedelta(days=1):
            current += 1
            longest = max(longest, current)
        else:
            current = 1

    return longest


def _get_session_speech_metrics(user_id: int) -> dict:
    """Derive pace and fluency signals from the user's completed sessions.

    Filler-word maps are stored as JSON, so the totals are summed in Python over
    a single projected query rather than one query per session.
    """
    rows = _completed_sessions_query(user_id).options(
        load_only(
            InterviewSession.total_words_spoken,
            InterviewSession.total_speaking_time_seconds,
            InterviewSession.filler_word_counts,
        )
    ).all()

    total_words = 0
    total_seconds = 0.0
    total_fillers = 0
    filler_breakdown: dict[str, int] = {}
    has_ideal_pace_session = False
    has_low_filler_session = False

    for row in rows:
        words = row.total_words_spoken or 0
        seconds = row.total_speaking_time_seconds or 0.0
        fillers = row.filler_word_counts or {}
        session_fillers = sum(fillers.values())

        total_words += words
        total_seconds += seconds
        total_fillers += session_fillers

        for word, count in fillers.items():
            filler_breakdown[word] = filler_breakdown.get(word, 0) + count

        if seconds > 0:
            session_wpm = words / (seconds / 60.0)
            if IDEAL_WPM_RANGE[0] <= session_wpm <= IDEAL_WPM_RANGE[1]:
                has_ideal_pace_session = True

        if words >= MIN_WORDS_FOR_FLUENCY_BADGE and (session_fillers / words) < 0.01:
            has_low_filler_session = True

    average_wpm = int(round(total_words / (total_seconds / 60.0))) if total_seconds > 0 else 0
    filler_rate = (total_fillers / total_words) if total_words > 0 else 0.0

    return {
        'average_wpm': average_wpm,
        'total_words_spoken': total_words,
        'total_filler_words': total_fillers,
        'filler_rate': filler_rate,
        'filler_breakdown': dict(sorted(filler_breakdown.items(), key=lambda item: item[1], reverse=True)),
        'has_ideal_pace_session': has_ideal_pace_session,
        'has_low_filler_session': has_low_filler_session,
    }


def get_user_statistics(user_id: int) -> dict:
    """Aggregate the user's interview record into the statistics every page shares.

    Returns counts, score aggregates, streaks, and speech signals. Every value is
    computed from the user's own rows; users with no history receive zeros.
    """
    status_counts = db.session.query(
        func.count(InterviewSession.id),
        func.sum(case((InterviewSession.status == SESSION_STATUS_COMPLETED, 1), else_=0)),
        func.sum(case((InterviewSession.status == SESSION_STATUS_IN_PROGRESS, 1), else_=0)),
    ).filter(InterviewSession.user_id == user_id).one()

    total_sessions = status_counts[0] or 0
    completed_sessions = status_counts[1] or 0
    in_progress_sessions = status_counts[2] or 0

    score_aggregates = db.session.query(
        func.avg(FeedbackReport.overall_score),
        func.max(FeedbackReport.overall_score),
        func.count(FeedbackReport.id),
    ).join(
        InterviewSession, FeedbackReport.session_id == InterviewSession.id
    ).filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == SESSION_STATUS_COMPLETED,
    ).one()

    average_score = float(score_aggregates[0]) if score_aggregates[0] is not None else 0.0
    best_score = float(score_aggregates[1]) if score_aggregates[1] is not None else 0.0
    scored_sessions = score_aggregates[2] or 0

    max_company_sessions = db.session.query(
        func.count(InterviewSession.id)
    ).filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == SESSION_STATUS_COMPLETED,
        InterviewSession.company_name.isnot(None),
        InterviewSession.company_name != '',
    ).group_by(
        func.lower(InterviewSession.company_name)
    ).order_by(
        func.count(InterviewSession.id).desc()
    ).limit(1).scalar()

    practice_days = get_completed_session_dates(user_id)
    speech_metrics = _get_session_speech_metrics(user_id)

    statistics = {
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'in_progress_sessions': in_progress_sessions,
        'scored_sessions': scored_sessions,
        'average_score': round(average_score, 1),
        'best_score': round(best_score, 1),
        'current_streak': calculate_current_streak_from_dates(practice_days),
        'longest_streak': calculate_longest_streak_from_dates(practice_days),
        'practice_days': len(practice_days),
        'max_sessions_single_company': max_company_sessions or 0,
    }
    statistics.update(speech_metrics)
    return statistics


def get_category_averages(user_id: int) -> list[dict]:
    """Average each feedback category across the user's scored interviews.

    Returns one entry per category, ordered strongest first, or an empty list when
    the user has no feedback reports yet.
    """
    columns = [func.avg(getattr(FeedbackReport, column)) for column, _ in SCORE_CATEGORIES]

    row = db.session.query(*columns).join(
        InterviewSession, FeedbackReport.session_id == InterviewSession.id
    ).filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == SESSION_STATUS_COMPLETED,
    ).one()

    averages = [
        {'key': column, 'label': label, 'average': round(float(value), 1)}
        for (column, label), value in zip(SCORE_CATEGORIES, row)
        if value is not None
    ]

    return sorted(averages, key=lambda item: item['average'], reverse=True)


def get_score_trend(user_id: int, limit: int = SCORE_TREND_LIMIT) -> list[dict]:
    """Return the user's most recent scored interviews in chronological order.

    Each point comes from a real ``FeedbackReport`` joined to its session, so the
    chart can only ever plot interviews the user actually completed.
    """
    rows = db.session.query(
        InterviewSession.id,
        InterviewSession.completed_at,
        InterviewSession.company_name,
        InterviewSession.job_role,
        FeedbackReport.overall_score,
    ).join(
        FeedbackReport, FeedbackReport.session_id == InterviewSession.id
    ).filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == SESSION_STATUS_COMPLETED,
        InterviewSession.completed_at.isnot(None),
    ).order_by(
        InterviewSession.completed_at.desc()
    ).limit(limit).all()

    trend = [
        {
            'session_id': row.id,
            'date': row.completed_at.strftime('%b %d'),
            'iso_date': row.completed_at.date().isoformat(),
            'score': round(float(row.overall_score or 0), 1),
            'company': row.company_name,
            'job_role': row.job_role,
        }
        for row in rows
    ]
    trend.reverse()
    return trend


def get_weekly_activity(user_id: int, weeks: int = 12) -> list[dict]:
    """Group completed interviews into ISO weeks using their real completion timestamps.

    Only weeks in which the user actually completed an interview are returned;
    missing weeks are never backfilled.
    """
    since = utc_now_naive() - timedelta(weeks=weeks)

    rows = db.session.query(
        func.date(InterviewSession.completed_at).label('day'),
        func.count(InterviewSession.id).label('sessions'),
        func.avg(FeedbackReport.overall_score).label('average_score'),
    ).outerjoin(
        FeedbackReport, FeedbackReport.session_id == InterviewSession.id
    ).filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == SESSION_STATUS_COMPLETED,
        InterviewSession.completed_at.isnot(None),
        InterviewSession.completed_at >= since,
    ).group_by('day').all()

    buckets: dict[date, dict] = {}
    for row in rows:
        day = _as_date(row.day)
        if day is None:
            continue
        week_start = day - timedelta(days=day.weekday())
        bucket = buckets.setdefault(
            week_start,
            {'week_start': week_start, 'sessions': 0, 'score_total': 0.0, 'scored': 0},
        )
        bucket['sessions'] += row.sessions or 0
        if row.average_score is not None:
            bucket['score_total'] += float(row.average_score) * (row.sessions or 0)
            bucket['scored'] += row.sessions or 0

    weekly = []
    for week_start in sorted(buckets):
        bucket = buckets[week_start]
        weekly.append({
            'week_start': week_start,
            'label': week_start.strftime('%b %d'),
            'sessions': bucket['sessions'],
            'average_score': round(bucket['score_total'] / bucket['scored'], 1) if bucket['scored'] else None,
        })

    return weekly


def get_recent_activity_comparison(user_id: int, window_days: int = ACTIVITY_WINDOW_DAYS) -> dict:
    """Compare the current rolling window against the one immediately before it.

    ``score_change`` is ``None`` unless both windows contain scored interviews, so
    no trend is claimed without two real data points to compare.
    """
    now = utc_now_naive()
    current_start = now - timedelta(days=window_days)
    previous_start = now - timedelta(days=window_days * 2)

    row = db.session.query(
        func.sum(case((InterviewSession.completed_at >= current_start, 1), else_=0)),
        func.avg(case((InterviewSession.completed_at >= current_start, FeedbackReport.overall_score))),
        func.sum(case((InterviewSession.completed_at < current_start, 1), else_=0)),
        func.avg(case((InterviewSession.completed_at < current_start, FeedbackReport.overall_score))),
    ).outerjoin(
        FeedbackReport, FeedbackReport.session_id == InterviewSession.id
    ).filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == SESSION_STATUS_COMPLETED,
        InterviewSession.completed_at.isnot(None),
        InterviewSession.completed_at >= previous_start,
    ).one()

    current_average = float(row[1]) if row[1] is not None else None
    previous_average = float(row[3]) if row[3] is not None else None

    score_change = None
    if current_average is not None and previous_average is not None:
        score_change = round(current_average - previous_average, 1)

    return {
        'window_days': window_days,
        'current_sessions': row[0] or 0,
        'previous_sessions': row[2] or 0,
        'current_average_score': round(current_average, 1) if current_average is not None else None,
        'previous_average_score': round(previous_average, 1) if previous_average is not None else None,
        'score_change': score_change,
    }


def get_recent_sessions(user_id: int, limit: int = 5) -> list[dict]:
    """Return the user's most recent interviews with their scores in a single query."""
    rows = db.session.query(
        InterviewSession.id,
        InterviewSession.job_role,
        InterviewSession.company_name,
        InterviewSession.interview_type,
        InterviewSession.status,
        InterviewSession.started_at,
        InterviewSession.completed_at,
        FeedbackReport.overall_score,
    ).outerjoin(
        FeedbackReport, FeedbackReport.session_id == InterviewSession.id
    ).filter(
        InterviewSession.user_id == user_id
    ).order_by(
        InterviewSession.started_at.desc()
    ).limit(limit).all()

    return [
        {
            'id': row.id,
            'job_role': row.job_role,
            'company_name': row.company_name,
            'interview_type': row.interview_type,
            'status': row.status,
            'started_at': row.started_at,
            'completed_at': row.completed_at,
            'score': int(round(row.overall_score)) if row.overall_score is not None else None,
            'is_completed': row.status == SESSION_STATUS_COMPLETED,
        }
        for row in rows
    ]


def get_skill_gap_summary(user_id: int, limit: int = 5) -> list[dict]:
    """Return the user's open skill gaps, most severe and most recent first.

    Repeated findings for the same skill are collapsed into a single entry with an
    occurrence count, so the UI reflects distinct weaknesses rather than duplicates.
    """
    rows = db.session.query(
        SkillGap.skill_name,
        SkillGap.severity,
        func.count(SkillGap.id).label('occurrences'),
        func.max(SkillGap.identified_at).label('last_identified_at'),
    ).filter(
        SkillGap.user_id == user_id
    ).group_by(
        SkillGap.skill_name, SkillGap.severity
    ).order_by(
        func.max(SkillGap.identified_at).desc()
    ).all()

    summary = [
        {
            'skill_name': row.skill_name,
            'severity': (row.severity or 'medium').lower(),
            'occurrences': row.occurrences,
            'last_identified_at': row.last_identified_at,
        }
        for row in rows
    ]

    summary.sort(key=lambda item: (SEVERITY_ORDER.get(item['severity'], 1), -item['occurrences']))
    return summary[:limit]


def get_active_resume(user_id: int) -> ResumeProfile | None:
    """Return the user's active resume profile, if one has been uploaded."""
    return ResumeProfile.query.filter_by(user_id=user_id, is_active=True).first()


def get_earned_badge_map(user_id: int) -> dict:
    """Map each earned badge type to its record, keeping the earliest award date."""
    badges = Badge.query.filter_by(user_id=user_id).order_by(Badge.earned_at.asc()).all()

    earned: dict[str, Badge] = {}
    for badge in badges:
        earned.setdefault(badge.badge_type, badge)
    return earned


def get_recent_badges(user_id: int, limit: int = 5) -> list[Badge]:
    """Return the badges the user earned most recently."""
    return Badge.query.filter_by(user_id=user_id)\
        .order_by(Badge.earned_at.desc()).limit(limit).all()


def build_achievements(user_id: int, statistics: dict | None = None) -> dict:
    """Evaluate every catalog achievement against the user's real statistics.

    An achievement is reported as earned when its condition holds for the user's
    current records. The earned date is taken from the stored ``Badge`` row that
    was written when the milestone was reached; if a condition is satisfied but no
    badge row exists yet (the awarding pass runs when an interview ends), the
    achievement is still shown as earned with no date rather than a fabricated one.
    """
    stats = statistics if statistics is not None else get_user_statistics(user_id)
    earned_badges = get_earned_badge_map(user_id)

    achievements = []
    for definition in BADGE_DEFINITIONS:
        badge = earned_badges.get(definition.badge_type)
        is_earned = definition.is_earned(stats)
        progress = definition.get_progress(stats)

        percent = 0
        if progress is not None and progress[1] > 0:
            percent = int(round(progress[0] / progress[1] * 100))
        if is_earned:
            percent = 100

        achievements.append({
            'badge_type': definition.badge_type,
            'name': definition.name,
            'description': definition.description,
            'icon': definition.icon,
            'is_earned': is_earned,
            'earned_at': badge.earned_at if badge else None,
            'progress_current': progress[0] if progress else None,
            'progress_target': progress[1] if progress else None,
            'progress_percent': percent,
        })

    achievements.sort(key=lambda item: (not item['is_earned'], -item['progress_percent']))
    earned_count = sum(1 for item in achievements if item['is_earned'])

    return {
        'achievements': achievements,
        'earned_count': earned_count,
        'total_count': TOTAL_BADGE_COUNT,
        'completion_percent': int(round(earned_count / TOTAL_BADGE_COUNT * 100)) if TOTAL_BADGE_COUNT else 0,
    }
