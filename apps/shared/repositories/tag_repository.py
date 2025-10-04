"""
Tag repository using pure functions for tag operations.
Following Zero-Trust UUID Architecture Phase 2 requirements.
"""
import sqlite3
from typing import Optional
from pathlib import Path
from contextlib import contextmanager

from apps.shared.config.database import DATABASE_PATH


# Pure function database utilities
@contextmanager
def get_tag_db_connection(db_path: Path = DATABASE_PATH):
    """
    Context manager for database connections.

    Args:
        db_path: Path to SQLite database

    Yields:
        sqlite3.Connection with row factory enabled
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def execute_tag_query(query: str, params: tuple = (), db_path: Path = DATABASE_PATH) -> list[sqlite3.Row]:
    """
    Execute SELECT query and return all results.

    Args:
        query: SQL query string
        params: Query parameters
        db_path: Database path

    Returns:
        List of Row objects
    """
    with get_tag_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def execute_tag_query_one(query: str, params: tuple = (), db_path: Path = DATABASE_PATH) -> Optional[sqlite3.Row]:
    """
    Execute SELECT query and return single result.

    Args:
        query: SQL query string
        params: Query parameters
        db_path: Database path

    Returns:
        Single Row object or None
    """
    with get_tag_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()


def execute_tag_command(command: str, params: tuple = (), db_path: Path = DATABASE_PATH) -> int:
    """
    Execute INSERT/UPDATE/DELETE command.

    Args:
        command: SQL command string
        params: Command parameters
        db_path: Database path

    Returns:
        Number of affected rows
    """
    with get_tag_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(command, params)
        conn.commit()
        return cursor.rowcount


# Tag operations as pure functions
def get_tag_by_id(tag_id: str, workspace_id: str, db_path: Path = DATABASE_PATH) -> Optional[dict]:
    """
    Get tag by ID with workspace isolation.

    Args:
        tag_id: Tag UUID
        workspace_id: Workspace UUID
        db_path: Database path

    Returns:
        Tag dict with keys: tag_id, name, workspace_id, card_count, created, modified, deleted
    """
    query = """
        SELECT tag_id, tag as name, workspace_id, card_count, created, modified, deleted
        FROM tags
        WHERE tag_id = ? AND workspace_id = ? AND deleted IS NULL
    """
    row = execute_tag_query_one(query, (tag_id, workspace_id), db_path)
    return dict(row) if row else None


def get_tag_by_name(name: str, workspace_id: str, db_path: Path = DATABASE_PATH) -> Optional[dict]:
    """
    Get tag by name with workspace isolation.

    Args:
        name: Tag name
        workspace_id: Workspace UUID
        db_path: Database path

    Returns:
        Tag dict or None
    """
    query = """
        SELECT tag_id, tag as name, workspace_id, card_count, created, modified, deleted
        FROM tags
        WHERE tag = ? AND workspace_id = ? AND deleted IS NULL
    """
    row = execute_tag_query_one(query, (name, workspace_id), db_path)
    return dict(row) if row else None


def list_tags_by_workspace(workspace_id: str, limit: int = 1000, db_path: Path = DATABASE_PATH) -> list[dict]:
    """
    List all non-deleted tags in workspace.

    Args:
        workspace_id: Workspace UUID
        limit: Maximum number of tags to return
        db_path: Database path

    Returns:
        List of tag dicts
    """
    query = """
        SELECT tag_id, tag as name, workspace_id, card_count, created, modified, deleted
        FROM tags
        WHERE workspace_id = ? AND deleted IS NULL
        ORDER BY tag ASC
        LIMIT ?
    """
    rows = execute_tag_query(query, (workspace_id, limit), db_path)
    return [dict(row) for row in rows]


def get_tag_counts(workspace_id: str, db_path: Path = DATABASE_PATH) -> dict[str, int]:
    """
    Get card_count for all non-deleted tags in workspace.

    Args:
        workspace_id: Workspace UUID
        db_path: Database path

    Returns:
        Dict mapping tag_id to card_count
    """
    query = """
        SELECT tag_id, card_count
        FROM tags
        WHERE workspace_id = ? AND deleted IS NULL
    """
    rows = execute_tag_query(query, (workspace_id,), db_path)
    return {row["tag_id"]: row["card_count"] for row in rows}


def create_tag(tag_id: str, name: str, workspace_id: str, db_path: Path = DATABASE_PATH) -> dict:
    """
    Create new tag. Triggers auto-fill created and modified.

    Args:
        tag_id: Tag UUID
        name: Tag name
        workspace_id: Workspace UUID
        db_path: Database path

    Returns:
        Created tag dict
    """
    command = """
        INSERT INTO tags (tag_id, tag, workspace_id, card_count, user_id, tag_bitmap, created, modified)
        VALUES (?, ?, ?, 0, 'default-user', 0, datetime('now'), datetime('now'))
    """
    execute_tag_command(command, (tag_id, name, workspace_id), db_path)

    return get_tag_by_id(tag_id, workspace_id, db_path)


def soft_delete_tag(tag_id: str, workspace_id: str, db_path: Path = DATABASE_PATH) -> bool:
    """
    Soft delete tag (sets deleted timestamp). Trigger auto-updates modified.

    Args:
        tag_id: Tag UUID
        workspace_id: Workspace UUID
        db_path: Database path

    Returns:
        True if deleted, False if not found
    """
    command = """
        UPDATE tags
        SET deleted = datetime('now')
        WHERE tag_id = ? AND workspace_id = ? AND deleted IS NULL
    """
    rowcount = execute_tag_command(command, (tag_id, workspace_id), db_path)
    return rowcount > 0


def get_tag_card_count(tag_id: str, workspace_id: str, db_path: Path = DATABASE_PATH) -> int:
    """
    Get card count for a tag.

    Args:
        tag_id: Tag UUID
        workspace_id: Workspace UUID
        db_path: Database path

    Returns:
        Card count (0 if tag not found)
    """
    tag = get_tag_by_id(tag_id, workspace_id, db_path)
    return tag["card_count"] if tag else 0


# Backward compatibility class wrapper (TEMPORARY - to be removed)
class TagRepository:
    """
    DEPRECATED: Backward compatibility wrapper. Use pure functions instead.
    This class will be removed in Phase 2 completion.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DATABASE_PATH

    def get_by_id(self, tag_id: str, workspace_id: str) -> Optional[dict]:
        return get_tag_by_id(tag_id, workspace_id, self.db_path)

    def get_by_name(self, name: str, workspace_id: str) -> Optional[dict]:
        return get_tag_by_name(name, workspace_id, self.db_path)

    def list_by_workspace(self, workspace_id: str, limit: int = 1000) -> list[dict]:
        return list_tags_by_workspace(workspace_id, limit, self.db_path)

    def get_counts(self, workspace_id: str) -> dict[str, int]:
        return get_tag_counts(workspace_id, self.db_path)

    def create(self, tag_id: str, name: str, workspace_id: str) -> dict:
        return create_tag(tag_id, name, workspace_id, self.db_path)

    def soft_delete(self, tag_id: str, workspace_id: str) -> bool:
        return soft_delete_tag(tag_id, workspace_id, self.db_path)

    def get_card_count(self, tag_id: str, workspace_id: str) -> int:
        return get_tag_card_count(tag_id, workspace_id, self.db_path)
