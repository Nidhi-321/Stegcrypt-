# backend/config.py
import os
from datetime import timedelta
from logging.config import dictConfig

class BaseConfig:
    DEBUG = False
    TESTING = False
    # general
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-prod")
    JSONIFY_PRETTYPRINT_REGULAR = False

    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://dbuser:dbpass@127.0.0.1:5432/stegcrypt",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # tune pool for production
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": int(os.getenv("DB_POOL_SIZE", 10)),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", 20)),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", 30)),
    }

    # Redis / Memurai for caching, rate-limiting, session store
    REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    RATELIMIT_STORAGE_URL = os.getenv("RATELIMIT_STORAGE_URL", REDIS_URL)

    # Flask-Limiter
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_DEFAULT = "200 per minute"

    # Waitress / Server
    WAITRESS_THREADS = int(os.getenv("WAITRESS_THREADS", 8))
    WAITRESS_PORT = int(os.getenv("PORT", 8000))

    # Health check
    HEALTH_PATH = os.getenv("HEALTH_PATH", "/healthz")

    # Logging (defaults to stdout)
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

class ProductionConfig(BaseConfig):
    DEBUG = False
    # production-specific
    SESSION_COOKIE_SECURE = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

def configure_logging():
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            },
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "handlers": ["stdout"],
            "level": level,
        },
    })
