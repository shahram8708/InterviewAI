"""
Configuration classes for the AI Mock Interview Platform.
All values are read from environment variables via a central Config hierarchy.
"""
import os
from cryptography.fernet import Fernet

_basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    """Base configuration — shared across all environments."""
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-me')
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key().decode())
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(_basedir, 'instance', 'app.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_TYPE = os.environ.get('SESSION_TYPE', 'filesystem')
    SESSION_FILE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'sessions')
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_SIZE_MB', 10)) * 1024 * 1024
    MAX_UPLOAD_SIZE_MB = int(os.environ.get('MAX_UPLOAD_SIZE_MB', 10))
    MAX_PDF_PAGES = 10
    RATE_LIMIT_LOGIN = os.environ.get('RATE_LIMIT_LOGIN_PER_HOUR', '10') + '/hour'
    RATE_LIMIT_RESUME = os.environ.get('RATE_LIMIT_RESUME_UPLOADS_PER_DAY', '10') + '/day'
    RATE_LIMIT_API = os.environ.get('RATE_LIMIT_API_CALLS_PER_MINUTE', '60') + '/minute'
    ENABLE_INSTITUTION_BRANDING = os.environ.get('ENABLE_INSTITUTION_BRANDING', 'false').lower() == 'true'
    INSTITUTION_NAME = os.environ.get('INSTITUTION_NAME', '')
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'uploads')
    GEMINI_MODEL = 'gemini-2.5-flash'


class DevelopmentConfig(Config):
    """Development-specific overrides."""
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production-specific overrides."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Strict'


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
