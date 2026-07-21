"""
User model — stores identity, encrypted API key, and preferences.
"""
from datetime import datetime, timezone
from app.extensions import db


class User(db.Model):
    """Represents a platform user identified by name + encrypted Gemini API key."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    encrypted_api_key = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    theme_preference = db.Column(db.String(20), default='system')
    high_contrast = db.Column(db.Boolean, default=False)
    reduced_motion = db.Column(db.Boolean, default=False)
    speech_locale = db.Column(db.String(20), default='en-US')
    voice_speed = db.Column(db.Float, default=1.0)

    resume_profiles = db.relationship('ResumeProfile', backref='user', lazy='dynamic',
                                       cascade='all, delete-orphan')
    interview_sessions = db.relationship('InterviewSession', backref='user', lazy='dynamic',
                                          cascade='all, delete-orphan')
    progress_snapshots = db.relationship('ProgressSnapshot', backref='user', lazy='dynamic',
                                          cascade='all, delete-orphan')
    badges = db.relationship('Badge', backref='user', lazy='dynamic',
                              cascade='all, delete-orphan')
    skill_gaps = db.relationship('SkillGap', backref='user', lazy='dynamic',
                                  cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.id}: {self.full_name}>'
