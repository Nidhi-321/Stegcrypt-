# config/production.py
"""
Production configuration for StegCrypt+ backend.

This file contains recommended production defaults.
For real deployments, override these via environment variables
(e.g., DATABASE_URL, SECRET_KEY, JWT_SECRET_KEY, RATELIMIT_STORAGE_URL).
"""

import os

# Database: prefer DATABASE_URL env var (Postgres/other) — example:
# export DATABASE_URL='postgresql://user:pass@dbhost:5432/stegcrypt'
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", None)

# Security
SECRET_KEY = os.environ.get("SECRET_KEY", "please-change-this-secret")
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "please-change-this-jwt-secret")

# Flask-Limiter (Redis recommended)
RATELIMIT_STORAGE_URL = os.environ.get("RATELIMIT_STORAGE_URL", None)

# SQLAlchemy
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Other config
PROPAGATE_EXCEPTIONS = True
