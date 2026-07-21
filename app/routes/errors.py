"""
Custom error handlers — rendered as on-brand error pages.
These functions are registered with the app via register_error_handler in __init__.py.
"""
from flask import Blueprint, render_template

errors_bp = Blueprint('errors', __name__)


def handle_400(e):
    """Bad Request error page."""
    return render_template('errors/400.html'), 400


def handle_404(e):
    """Not Found error page."""
    return render_template('errors/404.html'), 404


def handle_413(e):
    """File Too Large error page."""
    return render_template('errors/413.html'), 413


def handle_500(e):
    """Internal Server Error page — never shows a stack trace."""
    return render_template('errors/500.html'), 500
