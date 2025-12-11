from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from flask_migrate import Migrate
from flask import Flask
import redis
import os

Base = declarative_base()
_db_engine = None
SessionLocal = None

def init_db(app: Flask):
    global _db_engine, SessionLocal
    database_url = app.config['SQLALCHEMY_DATABASE_URI']
    # create engine with pool sizing suitable for production
    _db_engine = create_engine(
        database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        future=True
    )
    SessionLocal = scoped_session(sessionmaker(bind=_db_engine, autoflush=False, autocommit=False))
    # alembic will use the same engine via env.py when configured
    return _db_engine, SessionLocal

# Redis / Memurai client factory (uses redis-py)
_redis_client = None
def get_redis(app=None):
    global _redis_client
    if _redis_client is None:
        url = (app.config['REDIS_URL'] if app else os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0'))
        _redis_client = redis.from_url(url, decode_responses=True)
    return _redis_client
