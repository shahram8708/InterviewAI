"""
ResumeProfile model — stores the structured profile extracted from a user's PDF resume.
"""
from datetime import datetime, timezone
from app.extensions import db


class ResumeProfile(db.Model):
    """Structured resume data extracted via Gemini vision analysis."""
    __tablename__ = 'resume_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)
    skills = db.Column(db.JSON, default=list)
    education = db.Column(db.JSON, default=list)
    experience = db.Column(db.JSON, default=list)
    projects = db.Column(db.JSON, default=list)
    certifications = db.Column(db.JSON, default=list)
    technologies = db.Column(db.JSON, default=list)
    strengths = db.Column(db.JSON, default=list)
    career_level = db.Column(db.String(50), default='entry')
    summary = db.Column(db.Text, default='')
    raw_extracted_text = db.Column(db.Text, default='')

    interview_sessions = db.relationship('InterviewSession', backref='resume_profile', lazy='dynamic')

    def to_context_dict(self):
        """Return a compact dict suitable for the AI context engine."""
        return {
            'skills': self.skills or [],
            'education': self.education or [],
            'experience': self.experience or [],
            'projects': self.projects or [],
            'certifications': self.certifications or [],
            'technologies': self.technologies or [],
            'strengths': self.strengths or [],
            'career_level': self.career_level,
            'summary': self.summary,
        }

    def __repr__(self):
        return f'<ResumeProfile {self.id}: {self.original_filename}>'
