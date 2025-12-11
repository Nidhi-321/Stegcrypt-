from __future__ import with_statement
import os, sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# PROJECT_ROOT is the directory that contains 'alembic' (i.e. backend/)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REPO_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT, '..'))  # parent of backend/

# Ensure repo root is on sys.path so 'backend' is importable as a package
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Try to load .env
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJECT_ROOT, '.env'))
except Exception:
    pass

config = context.config

# Prefer environment variable
database_url = os.getenv('DATABASE_URL')
if database_url:
    config.set_main_option('sqlalchemy.url', database_url)

# debugging
print("=== ALEMBIC DEBUG START ===")
print("os.getenv('DATABASE_URL') ->", os.getenv('DATABASE_URL'))
print("config.get_main_option('sqlalchemy.url') ->", config.get_main_option('sqlalchemy.url'))
print("sys.path[0] ->", sys.path[0])
print("REPO_ROOT ->", REPO_ROOT)
print("PROJECT_ROOT ->", PROJECT_ROOT)
print("=== ALEMBIC DEBUG CONTINUING ===")

fileConfig(config.config_file_name)

# import your metadata
try:
    from backend.extensions import Base
    target_metadata = Base.metadata
    print("Imported Base metadata from backend.extensions")
except Exception as e:
    print("ERROR importing Base from backend.extensions:", e)
    raise

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
print("=== ALEMBIC DEBUG END ===")
