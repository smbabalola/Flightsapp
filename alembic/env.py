from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

def get_url():
    return os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/sureflights")

from app.db.session import Base  # noqa: E402
from app.models.models import *  # noqa: F401,F403

def run_migrations_offline():
    url = get_url()
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        {"sqlalchemy.url": get_url()},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
