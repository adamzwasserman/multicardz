"""Configuration package for MultiCardz."""
from .database import DATABASE_PATH, validate_database_path

__all__ = ['DATABASE_PATH', 'validate_database_path']
