"""
Real-time auto-migration middleware system.
High-performance pure-function implementation.
"""
from .types import (
    SchemaErrorCategory,
    SchemaError,
    Migration,
    MigrationResult,
)

__all__ = [
    "SchemaErrorCategory",
    "SchemaError",
    "Migration",
    "MigrationResult",
]
