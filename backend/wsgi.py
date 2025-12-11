# backend/wsgi.py
import os
from flask import Flask, jsonify
from config import ProductionConfig, configure_logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy

# shared extensions
db = SQLAlchemy()
limiter = None

def create_app(config_object=ProductionConfig):
    configure_logging()
    app = Flask(__name__, static_folder="static")
    app.config.from_object(config_object)

    # init extensions
    db.init_app(app)

    # limiter uses storage uri from config (Redis/Memurai recommended)
    global limiter
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        storage_uri=app.config.get("RATELIMIT_STORAGE_URL", "memory://"),
    )

    # basic health route
    @app.route(app.config.get("HEALTH_PATH", "/healthz"))
    def health():
        return jsonify({"status": "ok"}), 200

    # import/register your blueprints here
    try:
        # keep this import local so app factory doesn't import everything eagerly
        from .views import main_blueprint  # adjust if you have another module
        app.register_blueprint(main_blueprint)
    except Exception:
        # if you don't have a blueprint, ignore; just ensure import errors surface earlier in dev
        pass

    return app

# top-level app variable required by waitress: wsgi:app
app = create_app()
