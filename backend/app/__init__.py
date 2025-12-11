# app/__init__.py
import os
from flask import Flask
from .extensions import db, migrate, jwt, limiter, cors, init_socketio
from . import routes  # routes will be registered inside create_app()
from dotenv import load_dotenv

# Load .env if present (safe to call)
load_dotenv()

def create_app(config_object=None):
    """
    Application factory. Keeps initialization safe for CLI use.
    - config_object can be a config object or path to config
    """
    app = Flask(__name__, instance_relative_config=False)

    # Basic safe defaults; override via config_object or env
    app.config.setdefault("SECRET_KEY", os.environ.get("SECRET_KEY", "dev-secret-change-me"))
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", os.environ.get("DATABASE_URL", "sqlite:///app.db"))
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    # Limiters / CORS settings
    app.config.setdefault("CORS_ALLOWED_ORIGINS", os.environ.get("CORS_ALLOWED_ORIGINS", "*"))
    app.config.setdefault("JWT_SECRET_KEY", os.environ.get("JWT_SECRET_KEY", app.config["SECRET_KEY"]))

    # Allow passing a full config object
    if config_object:
        if isinstance(config_object, str):
            app.config.from_pyfile(config_object, silent=True)
        else:
            app.config.from_object(config_object)

    # Initialize standard extensions (safe for CLI)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": app.config["CORS_ALLOWED_ORIGINS"]}})

    # Register routes (routes module should be defensive about socketio)
    try:
        from .routes import register_routes
        register_routes(app)
    except Exception as exc:
        # If routes import fails for some reason, log and continue
        app.logger.exception("Failed registering routes during create_app(): %s", exc)

    # Attempt to initialize SocketIO lazily. This may fail if package versions are not aligned.
    # We intentionally do not raise here to keep CLI commands working.
    try:
        init_socketio(app)  # this will log warnings on failure
    except Exception as exc:
        # Already handled in init_socketio, but be defensive
        app.logger.warning("init_socketio raised an exception: %s", exc)

    return app
