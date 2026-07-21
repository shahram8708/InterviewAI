"""
Feedback, progress, badge, and skill gap models.
"""
from datetime import datetime, timezone
from app.extensions import db


class FeedbackReport(db.Model):
    """Post-interview analytics and detailed feedback, one-to-one with InterviewSession."""
    __tablename__ = 'feedback_reports'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('interview_sessions.id'), unique=True, nullable=False)
    overall_score = db.Column(db.Float, default=0.0)
    communication_score = db.Column(db.Float, default=0.0)
    technical_score = db.Column(db.Float, default=0.0)
    confidence_score = db.Column(db.Float, default=0.0)
    problem_solving_score = db.Column(db.Float, default=0.0)
    leadership_score = db.Column(db.Float, default=0.0)
    behavioral_score = db.Column(db.Float, default=0.0)
    strengths = db.Column(db.JSON, default=list)
    weaknesses = db.Column(db.JSON, default=list)
    missed_opportunities = db.Column(db.JSON, default=list)
    suggested_answers = db.Column(db.JSON, default=list)
    company_specific_recommendations = db.Column(db.JSON, default=list)
    improvement_plan = db.Column(db.JSON, default=list)
    resume_suggestions = db.Column(db.JSON, default=list)
    communication_insights = db.Column(db.JSON, default=dict)
    generated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<FeedbackReport session={self.session_id} score={self.overall_score}>'


class ProgressSnapshot(db.Model):
    """Weekly/periodic performance summary for trend tracking."""
    __tablename__ = 'progress_snapshots'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    period_start_date = db.Column(db.Date, nullable=False)
    sessions_completed = db.Column(db.Integer, default=0)
    average_score = db.Column(db.Float, default=0.0)
    streak_count = db.Column(db.Integer, default=0)
    filler_word_counts = db.Column(db.JSON, default=dict)
    average_speaking_speed_wpm = db.Column(db.Float, default=0.0)
    generated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<ProgressSnapshot user={self.user_id} week={self.period_start_date}>'


class Badge(db.Model):
    """Achievement badge earned by a user."""
    __tablename__ = 'badges'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    badge_type = db.Column(db.String(50), nullable=False)
    badge_name = db.Column(db.String(100), nullable=False)
    badge_description = db.Column(db.String(255), default='')
    badge_icon = db.Column(db.String(10), default='🏆')
    earned_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Badge {self.badge_type} user={self.user_id}>'


class SkillGap(db.Model):
    """Identified skill gap from interview performance patterns."""
    __tablename__ = 'skill_gaps'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    severity = db.Column(db.String(20), default='medium')
    details = db.Column(db.Text, default='')
    identified_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    related_session_id = db.Column(db.Integer, db.ForeignKey('interview_sessions.id'), nullable=True)

    related_session = db.relationship('InterviewSession', backref='skill_gaps_found')

    def __repr__(self):
        return f'<SkillGap {self.skill_name} severity={self.severity}>'


class CompanyPack(db.Model):
    """Curated interview preparation pack for a specific company."""
    __tablename__ = 'company_packs'

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.Text, default='')
    interview_tips = db.Column(db.JSON, default=list)
    common_questions = db.Column(db.JSON, default=list)
    culture_notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<CompanyPack {self.company_name}>'
