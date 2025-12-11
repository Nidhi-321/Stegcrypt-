import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, request
from .config import ProdConfig, DevConfig
from .extensions import init_db, get_redis, Base
from .routes import api_bp
import os

def create_app(config_name=None):
    app = Flask(__name__, static_folder=None)
    # environment selection
    env = os.getenv("FLASK_ENV", "production")
    app.config.from_object(DevConfig if env == "development" else ProdConfig)

    # init db and redis
    engine, SessionLocal = init_db(app)
    redis_client = get_redis(app)

    # register blueprints
    app.register_blueprint(api_bp, url_prefix="/api")

    # logging
    setup_logging(app)

    # simple health check
    @app.route("/healthz")
    def health():
        return jsonify(status="ok")

    # error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error="not_found"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Internal server error")
        return jsonify(error="internal_server_error"), 500

    return app

def setup_logging(app):
    log_level = logging.INFO if not app.config.get("DEBUG") else logging.DEBUG
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Console handler already present in many platforms; add rotating file
    handler = RotatingFileHandler("backend.log", maxBytes=10*1024*1024, backupCount=5)
    fmt = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    handler.setFormatter(fmt)
    logger.addHandler(handler)
