"""
Model package — imports all models so SQLAlchemy can discover them.
"""
from app.models.user import User
from app.models.resume import ResumeProfile
from app.models.interview import InterviewSession, InterviewTurn
from app.models.feedback import FeedbackReport, ProgressSnapshot, Badge, SkillGap, CompanyPack

__all__ = [
    'User', 'ResumeProfile', 'InterviewSession', 'InterviewTurn',
    'FeedbackReport', 'ProgressSnapshot', 'Badge', 'SkillGap', 'CompanyPack'
]
