"""
Database schema creation functions for multicardz zero-trust architecture.
Pure functions for creating database schemas across different modes.
NO CLASSES - only pure functions with explicit dependencies.
"""

import sqlite3
from typing import Optional, Any
import json
import uuid
from datetime import datetime


def create_zero_trust_schema(connection: sqlite3.Connection, mode: str) -> None:
    """
    Create the zero-trust database schema based on mode.

    Args:
        connection: SQLite database connection
        mode: Database mode ('development', 'normal', 'privacy')
    """
    cursor = connection.cursor()

    # Create cards table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            card_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            workspace_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            created DATETIME DEFAULT CURRENT_TIMESTAMP,
            modified DATETIME DEFAULT CURRENT_TIMESTAMP,
            deleted DATETIME,
            tag_ids TEXT NOT NULL DEFAULT '[]',  -- JSON array of tag UUIDs
            tag_bitmaps TEXT DEFAULT '[]'  -- JSON array of tag integer bitmaps
        )
    """)

    # Create indexes for cards
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_user_workspace ON cards(user_id, workspace_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cards_workspace_created ON cards(workspace_id, created)")

    # Create tags table with card_count
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            tag_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            workspace_id TEXT NOT NULL,
            name TEXT NOT NULL,
            tag_bitmap INTEGER NOT NULL,
            card_count INTEGER NOT NULL DEFAULT 0,  -- Auto-maintained count
            created DATETIME DEFAULT CURRENT_TIMESTAMP,
            modified DATETIME DEFAULT CURRENT_TIMESTAMP,
            deleted DATETIME
        )
    """)

    # Create indexes for tags
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_user_workspace ON tags(user_id, workspace_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_workspace_name ON tags(workspace_id, name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_bitmap ON tags(tag_bitmap)")

    # Create card_contents table for polymorphic content
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS card_contents (
            id TEXT PRIMARY KEY,
            card_id TEXT NOT NULL,
            type INTEGER NOT NULL,  -- 1=text, 2=number, 3=boolean, 4=json, 5=combined
            label TEXT,
            value_text TEXT,
            value_number REAL,
            value_boolean INTEGER,
            value_json TEXT,  -- JSON stored as TEXT in SQLite
            created DATETIME DEFAULT CURRENT_TIMESTAMP,
            modified DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (card_id) REFERENCES cards(card_id) ON DELETE CASCADE
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_card_contents_card_id ON card_contents(card_id)")

    # Create user_preferences table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id TEXT PRIMARY KEY,
            start_cards_visible INTEGER DEFAULT 1,
            start_cards_expanded INTEGER DEFAULT 0,
            show_tag_colors INTEGER DEFAULT 1,
            theme TEXT DEFAULT 'system',
            font_family TEXT DEFAULT 'Inter',
            separate_user_ai_tags INTEGER DEFAULT 1,
            stack_tags_vertically INTEGER DEFAULT 0,
            created DATETIME DEFAULT CURRENT_TIMESTAMP,
            modified DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create saved_views table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_views (
            view_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            workspace_id TEXT NOT NULL,
            name TEXT NOT NULL,
            tags_in_play TEXT NOT NULL DEFAULT '[]',  -- JSON array of tag combinations
            created DATETIME DEFAULT CURRENT_TIMESTAMP,
            modified DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_preferences(user_id) ON DELETE CASCADE
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_saved_views_user_workspace ON saved_views(user_id, workspace_id)")

    # Create triggers for auto-updating modified timestamp
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_cards_modified
        AFTER UPDATE ON cards
        FOR EACH ROW
        BEGIN
            UPDATE cards SET modified = CURRENT_TIMESTAMP WHERE card_id = NEW.card_id;
        END
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_tags_modified
        AFTER UPDATE ON tags
        FOR EACH ROW
        BEGIN
            UPDATE tags SET modified = CURRENT_TIMESTAMP WHERE tag_id = NEW.tag_id;
        END
    """)

    connection.commit()


def create_privacy_mode_schemas(
    browser_conn: sqlite3.Connection,
    server_conn: sqlite3.Connection,
    user_id: str,
    workspace_id: str
) -> None:
    """
    Create privacy mode schemas for three-way sync architecture.

    Args:
        browser_conn: Browser database connection (full content)
        server_conn: Server database connection (obfuscated only)
        user_id: User ID for isolation
        workspace_id: Workspace ID for isolation
    """
    # Browser database gets full schema
    create_zero_trust_schema(browser_conn, 'privacy')

    # Server database gets obfuscated schema only
    cursor = server_conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS obfuscated_cards (
            card_bitmap INTEGER PRIMARY KEY,
            tag_bitmaps TEXT,  -- JSON array of tag bitmaps
            checksum TEXT,
            sync_version INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS obfuscated_tags (
            tag_bitmap INTEGER PRIMARY KEY,
            checksum TEXT,
            sync_version INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_metadata (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at INTEGER
        )
    """)

    # Insert initial metadata
    cursor.execute("""
        INSERT OR REPLACE INTO sync_metadata (key, value, updated_at)
        VALUES ('user_workspace', ?, strftime('%s', 'now'))
    """, (json.dumps({'user_id': user_id, 'workspace_id': workspace_id}),))

    server_conn.commit()


def create_user_workspace_database(
    connection: sqlite3.Connection,
    user_id: str,
    workspace_id: str
) -> None:
    """
    Create a database for a specific user-workspace combination.

    Args:
        connection: Database connection
        user_id: User ID for isolation
        workspace_id: Workspace ID for isolation
    """
    # Create the standard schema
    create_zero_trust_schema(connection, 'development')

    # Add metadata for user-workspace isolation
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS database_metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cursor.execute("""
        INSERT OR REPLACE INTO database_metadata (key, value)
        VALUES ('user_id', ?), ('workspace_id', ?)
    """, (user_id, workspace_id))

    connection.commit()


def update_tag_card_count(
    connection: sqlite3.Connection,
    tag_id: str,
    delta: int
) -> int:
    """
    Update the card_count for a tag.

    Args:
        connection: Database connection
        tag_id: Tag ID to update
        delta: Change in count (+1 for add, -1 for remove)

    Returns:
        New card count
    """
    cursor = connection.cursor()

    # Update the count
    cursor.execute("""
        UPDATE tags
        SET card_count = MAX(0, card_count + ?)
        WHERE tag_id = ?
    """, (delta, tag_id))

    # Get the new count
    cursor.execute("SELECT card_count FROM tags WHERE tag_id = ?", (tag_id,))
    result = cursor.fetchone()

    connection.commit()

    return result[0] if result else 0


def maintain_tag_counts_on_card_update(
    connection: sqlite3.Connection,
    card_id: str,
    old_tag_ids: list,
    new_tag_ids: list
) -> None:
    """
    Maintain tag counts when a card's tags are updated.

    Args:
        connection: Database connection
        card_id: Card being updated
        old_tag_ids: Previous tag IDs
        new_tag_ids: New tag IDs
    """
    old_set = set(old_tag_ids)
    new_set = set(new_tag_ids)

    # Tags that were removed
    removed_tags = old_set - new_set
    for tag_id in removed_tags:
        update_tag_card_count(connection, tag_id, -1)

    # Tags that were added
    added_tags = new_set - old_set
    for tag_id in added_tags:
        update_tag_card_count(connection, tag_id, 1)


def generate_tag_bitmap(tag_name: str, workspace_id: str) -> int:
    """
    Generate a deterministic bitmap for a tag.

    Args:
        tag_name: Name of the tag
        workspace_id: Workspace ID for uniqueness

    Returns:
        Integer bitmap for the tag
    """
    # Use hash of tag name + workspace for deterministic bitmap
    import hashlib
    hash_input = f"{workspace_id}:{tag_name}".encode()
    hash_bytes = hashlib.md5(hash_input).digest()
    # Use first 4 bytes as 32-bit integer
    bitmap = int.from_bytes(hash_bytes[:4], byteorder='big')
    return bitmap & 0x7FFFFFFF  # Ensure positive integer