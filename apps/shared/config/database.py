"""
Database configuration for multicardz.

The database path is DYNAMIC and can be specified per-request via
tagsInPlay.controls.databasePath for multi-user environments.

This file provides the DEFAULT path when no path is specified.
"""
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)

# DEFAULT DATABASE PATH - Used when controls.databasePath is not specified
# Can be overridden by environment variable MULTICARDZ_DB_PATH
DEFAULT_DATABASE_PATH = Path(
    os.getenv("MULTICARDZ_DB_PATH", "/var/data/tutorial_customer.db")
)

# For backward compatibility, expose as DATABASE_PATH
DATABASE_PATH = DEFAULT_DATABASE_PATH

# Ensure directory exists for default path
DEFAULT_DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

logger.info(f"Default database path: {DEFAULT_DATABASE_PATH}")
logger.info(f"Database exists: {DEFAULT_DATABASE_PATH.exists()}")
