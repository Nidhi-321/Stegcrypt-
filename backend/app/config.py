# backend/app/config.py
import os
from datetime import timedelta

class Config:
    DEBUG = os.getenv("FLASK_ENV", "production") != "production"
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///data.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-jwt")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_SECONDS", "3600")))

    # CORS
    CORS_ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "*")  # set explicit in production

    # SocketIO
    SOCKETIO_ASYNC_MODE = os.getenv("SOCKETIO_ASYNC_MODE", "eventlet")

    # Rate limiting
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "200 per day;50 per hour")

    # Other
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
