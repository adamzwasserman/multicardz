"""
Card repository using pure functions for card operations.
Following Zero-Trust UUID Architecture Phase 2 requirements.
"""
import sqlite3
from typing import Optional
from pathlib import Path
from contextlib import contextmanager

from apps.shared.config.database import DATABASE_PATH


# Pure function database utilities
@contextmanager
def get_card_db_connection(db_path: Path = DATABASE_PATH):
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


def execute_card_query(query: str, params: tuple = (), db_path: Path = DATABASE_PATH) -> list[sqlite3.Row]:
    """
    Execute SELECT query and return all results.

    Args:
        query: SQL query string
        params: Query parameters
        db_path: Database path

    Returns:
        List of Row objects
    """
    with get_card_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def execute_card_query_one(query: str, params: tuple = (), db_path: Path = DATABASE_PATH) -> Optional[sqlite3.Row]:
    """
    Execute SELECT query and return single result.

    Args:
        query: SQL query string
        params: Query parameters
        db_path: Database path

    Returns:
        Single Row object or None
    """
    with get_card_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()


def execute_card_command(command: str, params: tuple = (), db_path: Path = DATABASE_PATH) -> int:
    """
    Execute INSERT/UPDATE/DELETE command.

    Args:
        command: SQL command string
        params: Command parameters
        db_path: Database path

    Returns:
        Number of affected rows
    """
    with get_card_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(command, params)
        conn.commit()
        return cursor.rowcount


# Card operations as pure functions
def get_card_by_id(card_id: str, workspace_id: str, db_path: Path = DATABASE_PATH) -> Optional[dict]:
    """
    Get card by ID with workspace isolation.

    Args:
        card_id: Card UUID
        workspace_id: Workspace UUID
        db_path: Database path

    Returns:
        Card dict with keys: card_id, name, workspace_id, tags, created, modified, deleted
    """
    query = """
        SELECT card_id, name, workspace_id, tags, created, modified, deleted
        FROM cards
        WHERE card_id = ? AND workspace_id = ? AND deleted IS NULL
    """
    row = execute_card_query_one(query, (card_id, workspace_id), db_path)
    return dict(row) if row else None


def list_cards_by_workspace(workspace_id: str, limit: int = 1000, db_path: Path = DATABASE_PATH) -> list[dict]:
    """
    List all non-deleted cards in workspace.

    Args:
        workspace_id: Workspace UUID
        limit: Maximum number of cards to return
        db_path: Database path

    Returns:
        List of card dicts
    """
    query = """
        SELECT card_id, name, workspace_id, tags, created, modified, deleted
        FROM cards
        WHERE workspace_id = ? AND deleted IS NULL
        ORDER BY created DESC
        LIMIT ?
    """
    rows = execute_card_query(query, (workspace_id, limit), db_path)
    return [dict(row) for row in rows]


def create_card(card_id: str, name: str, workspace_id: str, tag_ids: list[str], db_path: Path = DATABASE_PATH) -> dict:
    """
    Create new card with tags.

    Args:
        card_id: Card UUID
        name: Card name
        workspace_id: Workspace UUID
        tag_ids: List of tag UUIDs
        db_path: Database path

    Returns:
        Created card dict
    """
    # Convert tag_ids list to comma-separated string for inverted index
    tags_csv = ",".join(tag_ids) if tag_ids else ""

    # Insert card - trigger auto-calculates card_bitmap, triggers auto-maintain tag.card_count
    command = """
        INSERT INTO cards (card_id, name, workspace_id, tags, user_id, created, modified)
        VALUES (?, ?, ?, ?, 'default-user', datetime('now'), datetime('now'))
    """
    execute_card_command(command, (card_id, name, workspace_id, tags_csv), db_path)

    return get_card_by_id(card_id, workspace_id, db_path)


def update_card_title(card_id: str, workspace_id: str, title: str, db_path: Path = DATABASE_PATH) -> bool:
    """
    Update card title. Trigger auto-updates modified timestamp.

    Args:
        card_id: Card UUID
        workspace_id: Workspace UUID
        title: New title
        db_path: Database path

    Returns:
        True if updated, False if not found
    """
    command = """
        UPDATE cards
        SET name = ?
        WHERE card_id = ? AND workspace_id = ? AND deleted IS NULL
    """
    rowcount = execute_card_command(command, (title, card_id, workspace_id), db_path)
    return rowcount > 0


def update_card_content(card_id: str, workspace_id: str, content: str, db_path: Path = DATABASE_PATH) -> bool:
    """
    Update card description/content. Trigger auto-updates modified timestamp.

    Args:
        card_id: Card UUID
        workspace_id: Workspace UUID
        content: New description/content
        db_path: Database path

    Returns:
        True if updated, False if not found
    """
    command = """
        UPDATE cards
        SET description = ?
        WHERE card_id = ? AND workspace_id = ? AND deleted IS NULL
    """
    rowcount = execute_card_command(command, (content, card_id, workspace_id), db_path)
    return rowcount > 0


def add_tag_to_card(card_id: str, workspace_id: str, tag_id: str, db_path: Path = DATABASE_PATH) -> bool:
    """
    Add tag to card (updates comma-separated tags column). Trigger auto-updates modified.

    Args:
        card_id: Card UUID
        workspace_id: Workspace UUID
        tag_id: Tag UUID to add
        db_path: Database path

    Returns:
        True if added, False if not found or already present
    """
    # Get current tags
    card = get_card_by_id(card_id, workspace_id, db_path)
    if not card:
        return False

    current_tags = card["tags"].split(",") if card["tags"] else []

    # Check if tag already present
    if tag_id in current_tags:
        return False

    # Add tag
    current_tags.append(tag_id)
    new_tags_csv = ",".join(current_tags)

    command = """
        UPDATE cards
        SET tags = ?
        WHERE card_id = ? AND workspace_id = ? AND deleted IS NULL
    """
    rowcount = execute_card_command(command, (new_tags_csv, card_id, workspace_id), db_path)
    return rowcount > 0


def remove_tag_from_card(card_id: str, workspace_id: str, tag_id: str, db_path: Path = DATABASE_PATH) -> bool:
    """
    Remove tag from card (updates comma-separated tags column). Trigger auto-updates modified.

    Args:
        card_id: Card UUID
        workspace_id: Workspace UUID
        tag_id: Tag UUID to remove
        db_path: Database path

    Returns:
        True if removed, False if not found
    """
    # Get current tags
    card = get_card_by_id(card_id, workspace_id, db_path)
    if not card:
        return False

    current_tags = card["tags"].split(",") if card["tags"] else []

    # Check if tag present
    if tag_id not in current_tags:
        return False

    # Remove tag
    current_tags.remove(tag_id)
    new_tags_csv = ",".join(current_tags)

    command = """
        UPDATE cards
        SET tags = ?
        WHERE card_id = ? AND workspace_id = ? AND deleted IS NULL
    """
    rowcount = execute_card_command(command, (new_tags_csv, card_id, workspace_id), db_path)
    return rowcount > 0


def soft_delete_card(card_id: str, workspace_id: str, db_path: Path = DATABASE_PATH) -> bool:
    """
    Soft delete card (sets deleted timestamp). Trigger auto-updates modified.

    Args:
        card_id: Card UUID
        workspace_id: Workspace UUID
        db_path: Database path

    Returns:
        True if deleted, False if not found
    """
    command = """
        UPDATE cards
        SET deleted = datetime('now')
        WHERE card_id = ? AND workspace_id = ? AND deleted IS NULL
    """
    rowcount = execute_card_command(command, (card_id, workspace_id), db_path)
    return rowcount > 0


def get_card_tag_ids(card_id: str, workspace_id: str, db_path: Path = DATABASE_PATH) -> list[str]:
    """
    Get list of tag IDs for a card.

    Args:
        card_id: Card UUID
        workspace_id: Workspace UUID
        db_path: Database path

    Returns:
        List of tag UUIDs (empty if card not found)
    """
    card = get_card_by_id(card_id, workspace_id, db_path)
    if not card or not card["tags"]:
        return []

    return card["tags"].split(",")


# Backward compatibility class wrapper (TEMPORARY - to be removed)
class CardRepository:
    """
    DEPRECATED: Backward compatibility wrapper. Use pure functions instead.
    This class will be removed in Phase 2 completion.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DATABASE_PATH

    def get_by_id(self, card_id: str, workspace_id: str) -> Optional[dict]:
        return get_card_by_id(card_id, workspace_id, self.db_path)

    def list_by_workspace(self, workspace_id: str, limit: int = 1000) -> list[dict]:
        return list_cards_by_workspace(workspace_id, limit, self.db_path)

    def create(self, card_id: str, name: str, workspace_id: str, tag_ids: list[str]) -> dict:
        return create_card(card_id, name, workspace_id, tag_ids, self.db_path)

    def update_title(self, card_id: str, workspace_id: str, title: str) -> bool:
        return update_card_title(card_id, workspace_id, title, self.db_path)

    def update_content(self, card_id: str, workspace_id: str, content: str) -> bool:
        return update_card_content(card_id, workspace_id, content, self.db_path)

    def add_tag(self, card_id: str, workspace_id: str, tag_id: str) -> bool:
        return add_tag_to_card(card_id, workspace_id, tag_id, self.db_path)

    def remove_tag(self, card_id: str, workspace_id: str, tag_id: str) -> bool:
        return remove_tag_from_card(card_id, workspace_id, tag_id, self.db_path)

    def soft_delete(self, card_id: str, workspace_id: str) -> bool:
        return soft_delete_card(card_id, workspace_id, self.db_path)

    def get_tag_ids(self, card_id: str, workspace_id: str) -> list[str]:
        return get_card_tag_ids(card_id, workspace_id, self.db_path)
