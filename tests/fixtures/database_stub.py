"""
Database stub for testing group tags functionality.

Provides a simple in-memory SQLite database for testing without
requiring full database setup.
"""

import sqlite3
from contextlib import contextmanager
from typing import Generator

# Global test database connection
_test_db_connection = None


def get_connection() -> sqlite3.Connection:
    """
    Get test database connection.

    This is a stub function that returns an in-memory SQLite connection
    for testing purposes.
    """
    global _test_db_connection

    if _test_db_connection is None:
        _test_db_connection = sqlite3.connect(":memory:", check_same_thread=False)
        _initialize_test_schema(_test_db_connection)

    return _test_db_connection


def _initialize_test_schema(conn: sqlite3.Connection) -> None:
    """Initialize test database schema."""
    conn.executescript("""
        -- Group tags table
        CREATE TABLE IF NOT EXISTS group_tags (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            name TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            visual_style TEXT DEFAULT '{}',
            max_nesting_depth INTEGER DEFAULT 10,
            UNIQUE(workspace_id, name)
        );

        -- Group memberships
        CREATE TABLE IF NOT EXISTS group_memberships (
            group_id TEXT NOT NULL,
            member_tag_id TEXT NOT NULL,
            member_type TEXT NOT NULL CHECK (member_type IN ('tag', 'group')),
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            added_by TEXT NOT NULL,
            PRIMARY KEY (group_id, member_tag_id),
            FOREIGN KEY (group_id) REFERENCES group_tags(id) ON DELETE CASCADE,
            CHECK (group_id != member_tag_id)
        );

        -- Tags table (for testing tag existence)
        CREATE TABLE IF NOT EXISTS tags (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_group_tags_workspace ON group_tags(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_group_memberships_group ON group_memberships(group_id);
        CREATE INDEX IF NOT EXISTS idx_group_memberships_member ON group_memberships(member_tag_id);
    """)
    conn.commit()


def reset_test_database() -> None:
    """Reset the test database to empty state."""
    global _test_db_connection

    if _test_db_connection:
        _test_db_connection.close()
        _test_db_connection = None

    _test_db_connection = sqlite3.connect(":memory:", check_same_thread=False)
    _initialize_test_schema(_test_db_connection)


def close_test_database() -> None:
    """Close the test database connection."""
    global _test_db_connection

    if _test_db_connection:
        _test_db_connection.close()
        _test_db_connection = None
