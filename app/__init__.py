"""
Application factory for the AI Mock Interview Platform.
Creates and configures the Flask app, initializes extensions,
registers blueprints, and ensures the database exists on first run.
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, send_from_directory
from sqlalchemy.exc import SQLAlchemyError
from app.config import config_map
from app.extensions import db, csrf, limiter, sess, talisman


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map['default']))

    _ensure_directories(app)
    _init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _configure_logging(app)
    _register_template_helpers(app)
    _init_database(app)

    return app


def _ensure_directories(app):
    """Create required directories if they don't exist."""
    instance_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    os.makedirs(app.config.get('SESSION_FILE_DIR', os.path.join(instance_dir, 'sessions')), exist_ok=True)
    os.makedirs(app.config.get('UPLOAD_FOLDER', os.path.join(instance_dir, 'uploads')), exist_ok=True)


def _init_extensions(app):
    """Initialize all Flask extensions with the app."""
    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    sess.init_app(app)

    csp = {
        'default-src': ["'self'"],
        'script-src': ["'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net', 'https://fonts.googleapis.com'],
        'style-src': ["'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net', 'https://fonts.googleapis.com'],
        'font-src': ["'self'", 'https://fonts.gstatic.com', 'https://cdn.jsdelivr.net'],
        'img-src': ["'self'", 'data:', 'blob:'],
        'connect-src': ["'self'", 'https://cdn.jsdelivr.net'],
        'media-src': ["'self'", 'blob:'],
        'worker-src': ["'self'"],
    }

    talisman.init_app(
        app,
        force_https=not app.debug,
        content_security_policy=csp,
        content_security_policy_nonce_in=['script-src'],
        session_cookie_secure=not app.debug,
        frame_options='DENY',
        referrer_policy='strict-origin-when-cross-origin',
        x_content_type_options=True,
        x_xss_protection=True
    )

    @app.route('/sw.js')
    def service_worker():
        return send_from_directory(app.static_folder, 'sw.js', mimetype='application/javascript')


def _register_blueprints(app):
    """Register all application blueprints."""
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.resume import resume_bp
    from app.routes.interview import interview_bp
    from app.routes.analytics import analytics_bp
    from app.routes.api import api_bp
    from app.routes.errors import errors_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(resume_bp)
    app.register_blueprint(interview_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(errors_bp)


def _register_error_handlers(app):
    """Register custom error page handlers."""
    from app.routes.errors import handle_400, handle_404, handle_413, handle_500

    app.register_error_handler(400, handle_400)
    app.register_error_handler(404, handle_404)
    app.register_error_handler(413, handle_413)
    app.register_error_handler(500, handle_500)


def _register_template_helpers(app):
    """Register Jinja2 context processors and template filters."""
    from app.utils.helpers import format_duration, format_date, get_score_color

    @app.context_processor
    def inject_globals():
        """Inject global template variables available in every template."""
        return {
            'enable_branding': app.config.get('ENABLE_INSTITUTION_BRANDING', False),
            'institution_name': app.config.get('INSTITUTION_NAME', ''),
        }

    app.jinja_env.filters['format_duration'] = format_duration
    app.jinja_env.filters['format_date'] = format_date
    app.jinja_env.filters['score_color'] = get_score_color


def _configure_logging(app):
    """Set up rotating file and console logging, with key redaction."""
    from app.services.security_service import KeyRedactionFilter

    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )

    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10_000_000,
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.WARNING)
    file_handler.addFilter(KeyRedactionFilter())

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    console_handler.addFilter(KeyRedactionFilter())

    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)


def _init_database(flask_app):
    """Create all database tables on first run if they don't exist."""
    from app import models  # noqa: F401 — ensure all models are imported so create_all finds them
    with flask_app.app_context():
        db.create_all()
        _ensure_indexes(flask_app)
        flask_app.logger.info('Database tables verified/created.')


def _ensure_indexes(flask_app):
    """Create any model indexes missing from an already-existing database.

    create_all() only emits indexes alongside tables it creates, so databases
    provisioned before an index was declared would never receive it. Creating each
    index with checkfirst=True keeps startup idempotent for new and existing
    installations alike.
    """
    for table in db.metadata.sorted_tables:
        for index in table.indexes:
            try:
                index.create(bind=db.engine, checkfirst=True)
            except SQLAlchemyError:
                flask_app.logger.warning('Could not verify index %s.', index.name)
