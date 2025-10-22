"""
Alembic migration environment for multicardz™.

This module configures Alembic for database migrations with SQLite support.
"""

import logging
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add the project root to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Alembic Config object
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger('alembic.env')

# Target metadata (we'll define this based on our models)
target_metadata = None

def get_database_url() -> str:
    """Get database URL from environment or default."""
    import os

    # Try environment variable first
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        return db_url

    # Default to development database
    db_path = Path(__file__).parent.parent / "data" / "multicardz_dev.db"
    return f"sqlite:///{db_path}"

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine
    creation we don't even need a DBAPI to be available.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection
    with the context.
    """
    # Override the SQLAlchemy URL
    config.set_main_option('sqlalchemy.url', get_database_url())

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
