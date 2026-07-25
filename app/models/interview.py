"""
Interview models — InterviewSession and InterviewTurn.
"""
from datetime import datetime, timezone
from app.extensions import db


class InterviewSession(db.Model):
    """A single interview session with configuration, state, and compressed context."""
    __tablename__ = 'interview_sessions'

    # Analytics reads sessions by owner, by owner+status, and by owner+completion date;
    # these composite indexes keep the dashboard/progress aggregations index-only.
    __table_args__ = (
        db.Index('ix_interview_sessions_user_status', 'user_id', 'status'),
        db.Index('ix_interview_sessions_user_completed_at', 'user_id', 'completed_at'),
        db.Index('ix_interview_sessions_user_started_at', 'user_id', 'started_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resume_profile_id = db.Column(db.Integer, db.ForeignKey('resume_profiles.id'), nullable=False)
    job_role = db.Column(db.String(150), nullable=False)
    company_name = db.Column(db.String(150), nullable=False)
    experience_level = db.Column(db.String(50), nullable=False)
    interview_type = db.Column(db.String(50), nullable=False)
    interviewer_persona = db.Column(db.String(50), nullable=False, default='friendly')
    status = db.Column(db.String(20), nullable=False, default='in_progress')
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)
    compressed_context = db.Column(db.JSON, default=dict)
    company_research = db.Column(db.JSON, default=dict)
    question_categories_used = db.Column(db.JSON, default=dict)
    total_questions_target = db.Column(db.Integer, default=10)
    current_stage = db.Column(db.String(50), default='introduction')
    filler_word_counts = db.Column(db.JSON, default=dict)
    total_words_spoken = db.Column(db.Integer, default=0)
    total_speaking_time_seconds = db.Column(db.Float, default=0.0)

    turns = db.relationship('InterviewTurn', backref='session', lazy='dynamic',
                             cascade='all, delete-orphan', order_by='InterviewTurn.sequence_number')
    feedback_report = db.relationship('FeedbackReport', backref='session', uselist=False,
                                       cascade='all, delete-orphan')

    @property
    def turn_count(self):
        return self.turns.count()

    @property
    def avg_wpm(self):
        if self.total_speaking_time_seconds and self.total_speaking_time_seconds > 0:
            minutes = self.total_speaking_time_seconds / 60.0
            return int(self.total_words_spoken / minutes) if minutes > 0 else 0
        return 0

    @property
    def score(self):
        if self.feedback_report and self.feedback_report.overall_score is not None:
            return int(self.feedback_report.overall_score)
        return 0

    @property
    def company(self):
        return self.company_name or 'General'

    @property
    def date(self):
        if self.started_at:
            return self.started_at.strftime('%b %d, %Y')
        return 'Unknown Date'

    def __repr__(self):
        return f'<InterviewSession {self.id}: {self.job_role} at {self.company_name}>'


class InterviewTurn(db.Model):
    """A single question-answer exchange within an interview session."""
    __tablename__ = 'interview_turns'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('interview_sessions.id'), nullable=False)
    sequence_number = db.Column(db.Integer, nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_category = db.Column(db.String(50), default='role-specific')
    answer_text = db.Column(db.Text, default='')
    evaluation_label = db.Column(db.String(20), default='')
    ai_notes = db.Column(db.Text, default='')
    ai_response = db.Column(db.Text, default='')
    speaking_duration_seconds = db.Column(db.Float, default=0.0)
    word_count = db.Column(db.Integer, default=0)
    filler_words_in_turn = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<InterviewTurn {self.session_id}:{self.sequence_number}>'
