"""
Single source of truth for database configuration.
ALL database access MUST use this configuration.
"""
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# SINGLE SOURCE OF TRUTH - DO NOT DUPLICATE THIS PATH ANYWHERE
DATABASE_PATH = Path("/var/data/tutorial_customer.db")

# Ensure directory exists
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

logger.info(f"Database configuration initialized: {DATABASE_PATH}")
logger.info(f"Database exists: {DATABASE_PATH.exists()}")

def validate_database_path(path: Path) -> None:
    """Validate that a database path matches our single source of truth."""
    if path.resolve() != DATABASE_PATH.resolve():
        raise ValueError(
            f"Database path mismatch! "
            f"Expected: {DATABASE_PATH.resolve()}, "
            f"Got: {path.resolve()}. "
            f"ALL database access must use apps.shared.config.database.DATABASE_PATH"
        )
