from logging.config import fileConfig
import os
from sqlalchemy import create_engine
from alembic import context
from sqlmodel import SQLModel
import sys

# allow imports from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.models import *  # noqa: F401,F403 (defines models and registers metadata)

config = context.config
# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# use DATABASE_URL env var (fallback to sqlite)
db_url = os.getenv('DATABASE_URL', 'sqlite:///./dev.db')
# Alembic works with sync drivers; convert asyncpg URL to sync driver URL
sync_db_url = db_url.replace('+asyncpg', '')
config.set_main_option('sqlalchemy.url', sync_db_url)

target_metadata = SQLModel.metadata


def run_migrations_offline():
    context.configure(url=sync_db_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = create_engine(sync_db_url)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
