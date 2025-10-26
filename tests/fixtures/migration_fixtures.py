"""
Test fixtures for migration system.
Provides sample data and utilities for BDD tests.
"""
import pytest
import sqlite3
import sys
from pathlib import Path
from typing import Generator


@pytest.fixture
def sample_sqlite_errors():
    """Sample SQLite exceptions for testing error detection."""
    return {
        "no_table": sqlite3.OperationalError("no such table: bitmap_sequences"),
        "no_column": sqlite3.OperationalError("table cards has no column named card_bitmap"),
        "no_trigger": sqlite3.OperationalError("no such trigger: auto_calculate_card_bitmap"),
        "foreign_key": sqlite3.IntegrityError("FOREIGN KEY constraint failed"),
        "not_schema": ValueError("This is not a schema error")
    }


@pytest.fixture
def sample_migration_metadata():
    """Sample migration metadata for testing."""
    return {
        "version": 2,
        "sql_file": "002_add_bitmap_sequences.sql",
    }


@pytest.fixture
def memory_db() -> Generator[sqlite3.Connection, None, None]:
    """In-memory SQLite database for testing."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def test_workspace_id() -> str:
    """Test workspace UUID."""
    return "test-workspace-00000000-0000-0000-0000-000000000001"


@pytest.fixture
def test_user_id() -> str:
    """Test user UUID."""
    return "test-user-00000000-0000-0000-0000-000000000001"


@pytest.fixture
def migrations_dir(tmp_path: Path) -> Path:
    """Temporary directory with sample migration SQL files."""
    migrations = tmp_path / "migrations"
    migrations.mkdir()

    # Create sample migration file
    (migrations / "002_add_bitmap_sequences.sql").write_text(
        """
        CREATE TABLE bitmap_sequences (
            sequence_name TEXT PRIMARY KEY,
            current_value INTEGER NOT NULL DEFAULT 0
        );
        """
    )

    return migrations


def get_object_size(obj) -> int:
    """Get approximate size of Python object in bytes."""
    return sys.getsizeof(obj)


def measure_memory_usage(objects: list) -> int:
    """Measure total memory usage of a list of objects."""
    return sum(get_object_size(obj) for obj in objects)
