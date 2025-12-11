# app/extensions.py
"""
Central place for Flask extensions.
SocketIO import/initialization is deferred to avoid hard failure
during CLI operations (flask db migrate/upgrade etc.)
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

# SQLAlchemy / Migrate / JWT / Limiter / CORS created normally
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

# Limiter - uses in-memory storage by default; override config for production.
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

# CORS will be initialized per-app in create_app (so it can read app config)
cors = CORS()

# SocketIO will be created lazily because importing flask_socketio at module import
# time can break CLI commands if package versions mismatch. Keep a module-level
# variable that will be None until init_socketio() is called.
socketio = None  # type: ignore

def init_socketio(app, **kwargs):
    """
    Attempt to import and initialize flask_socketio.SocketIO.
    Returns the SocketIO instance on success, or None on failure.
    kwargs are passed to SocketIO(...) constructor.
    """
    global socketio
    if socketio is not None:
        return socketio

    try:
        # Import inside function to avoid top-level import-time errors
        from flask_socketio import SocketIO
        # Choose cors_allowed_origins from app config or default to '*'
        cors_allowed = app.config.get("CORS_ALLOWED_ORIGINS", "*")
        # Merge defaults with kwargs (kwargs override defaults)
        opts = {"cors_allowed_origins": cors_allowed}
        opts.update(kwargs or {})
        socketio = SocketIO(app, **opts)
        app.logger.info("SocketIO initialized successfully.")
        return socketio
    except Exception as exc:
        # Log a warning and continue without socket support
        app.logger.warning("SocketIO not available during init_socketio(): %s. Continuing without SocketIO.", exc)
        socketio = None
        return None
