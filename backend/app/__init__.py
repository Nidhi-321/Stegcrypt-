# app/__init__.py
"""
Application factory for StegCrypt+ backend.

Behavior:
- Loads configuration from (in priority):
    1) config_object dotted path passed to create_app()
    2) environment variable APP_CONFIG_FILE (dotted path or file)
    3) config/production.py (if exists)
    4) sensible defaults (including SQLite fallback DB)
- Initializes extensions: db, migrate, jwt, cors, limiter
- Attempts to initialize socketio (optional)
- Registers routes and health endpoint
- Returns either app or (app, socketio) depending on socket availability
"""

import os
import logging
from flask import Flask, jsonify, current_app

from .extensions import db, migrate, jwt, cors, init_limiter, init_socketio

# Configure basic logging for startup messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stegcrypt")

def _apply_defaults(app):
    """
    Apply safe default config values if not set by the environment or config file.
    Particularly ensures SQLALCHEMY_DATABASE_URI exists (SQLite fallback).
    """
    # Database config: prefer common DATABASE_URL env var, then SQLALCHEMY_DATABASE_URI, otherwise fallback to sqlite file
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("SQLALCHEMY_DATABASE_URI") or app.config.get("SQLALCHEMY_DATABASE_URI")
    if db_url:
        app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    else:
        # Fallback to a local sqlite file inside backend folder (safe default for single-node deployments/testing)
        sqlite_path = os.path.join(app.root_path, "..", "data", "stegcrypt.sqlite")
        # Ensure directory exists
        os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.abspath(sqlite_path)}"
        logger.info("No DATABASE_URL found — using SQLite fallback at %s", sqlite_path)

    # Other sane defaults (can be overridden)
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault("SECRET_KEY", os.environ.get("SECRET_KEY", app.config.get("SECRET_KEY", "replace-this-secret")))
    app.config.setdefault("JWT_SECRET_KEY", os.environ.get("JWT_SECRET_KEY", app.config.get("JWT_SECRET_KEY", "replace-this-jwt-secret")))

def create_app(config_object: str | None = None):
    """
    Create and configure the Flask application.
    Pass config_object as a dotted path (e.g. 'config.production') to load that config.
    """
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # 1) If a dotted config object is provided, load it
    if config_object:
        try:
            app.config.from_object(config_object)
            logger.info("Loaded config from object: %s", config_object)
        except Exception as e:
            logger.warning("Failed to load config object '%s': %s", config_object, e)

    # 2) Next, try APP_CONFIG_FILE env var (path or dotted object)
    app_cfg = os.environ.get("APP_CONFIG_FILE")
    if app_cfg:
        # Try dotted object import first
        try:
            app.config.from_object(app_cfg)
            logger.info("Loaded config from APP_CONFIG_FILE as object: %s", app_cfg)
        except Exception:
            # If that fails, try to treat it as a path to a python file with keys
            try:
                app.config.from_envvar("APP_CONFIG_FILE")
                logger.info("Loaded config from APP_CONFIG_FILE as file: %s", app_cfg)
            except Exception as e:
                logger.warning("Unable to load APP_CONFIG_FILE: %s (%s)", app_cfg, e)

    # 3) Try to load default config/production.py if present
    try:
        # import local config module if present
        import config.production as default_prod_cfg  # type: ignore
        try:
            app.config.from_object(default_prod_cfg)
            logger.info("Loaded default config from config/production.py")
        except Exception:
            pass
    except Exception:
        # not fatal — keep going
        pass

    # Apply safe defaults (ensures DB URI exists)
    _apply_defaults(app)

    # Initialize core extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)

    # Initialize limiter (reads RATELIMIT_STORAGE_URL from env/config)
    try:
        init_limiter(app)
    except Exception as e:
        logger.exception("init_limiter failed: %s", e)

    # Attempt to initialize SocketIO (optional)
    socketio = None
    try:
        socketio = init_socketio(app)
        if socketio is not None:
            # safe attempt to attach to app
            try:
                socketio.init_app(app, cors_allowed_origins="*")
                logger.info("SocketIO initialized")
            except Exception:
                logger.warning("SocketIO init_app raised an exception — continuing without socket support")
                socketio = None
    except Exception as e:
        # If init_socketio throws, continue without socketio
        logger.warning("SocketIO not available: %s", e)
        socketio = None

    # Register routes (import here to avoid circular imports)
    try:
        from . import routes as routes_module  # type: ignore
        routes_module.register_routes(app)
    except Exception as e:
        logger.exception("Failed to register routes: %s", e)

    # Health endpoint
    @app.route("/healthz")
    def healthz():
        return jsonify({"status": "ok"}), 200

    # Return either (app, socketio) or app
    if socketio is not None:
        return app, socketio
    return app
