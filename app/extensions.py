"""
Centralized Flask extension instances.
Initialized here, bound to the app in the factory function.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_session import Session
from flask_talisman import Talisman

db = SQLAlchemy()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=[])
sess = Session()
talisman = Talisman()
