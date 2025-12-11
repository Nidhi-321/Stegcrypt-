# app/extensions.py
"""
Central Flask extensions module.
Exports module-level extension objects so other modules can import them.

This file intentionally exposes:
    db, migrate, jwt, cors, limiter, socketio

socketio will be None until init_socketio(app) creates/assigns it.
"""
import logging
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Standard extensions exported for import elsewhere
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS(resources={r"/*": {"origins": "*"}})

# Global limiter instance (module-level)
# It will be configured against the app when init_limiter(app) is called.
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

# Module-level socketio variable exported for other modules to reference
# It will remain None until init_socketio(app) assigns an instance to it.
socketio = None

def init_limiter(app):
    """
    Initialize the module-level limiter with the Flask app.
    Flask-Limiter will check app.config['RATELIMIT_STORAGE_URL'] or the environment.
    """
    try:
        limiter.init_app(app)
    except Exception as e:
        logging.getLogger(__name__).exception("Failed to init limiter: %s", e)
        # fallback: limiter remains available (in-memory) so the app still runs

def init_socketio(app):
    """
    Try to create and return a Flask-SocketIO instance if libraries are present.
    Assign it to the module-level `socketio` so other modules can reference it as
    app.extensions.socketio. If SocketIO is not available or fails, return None.
    """
    global socketio
    try:
        from flask_socketio import SocketIO  # local import
    except Exception:
        # SocketIO not installed or incompatible — return None silently
        return None

    try:
        socketio = SocketIO(cors_allowed_origins="*")
        return socketio
    except Exception as e:
        logging.getLogger(__name__).exception("Failed to initialize SocketIO: %s", e)
        socketio = None
        return None
