#!/usr/bin/env python3
"""
multicardz™ Lesson Database Population Script
Populates the default database with lesson cards and tags for progressive onboarding.
"""

import json
import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

# Import lesson data and services
from apps.shared.data.onboarding_lessons import (
    get_default_lesson_state,
)
from apps.shared.services.lesson_service import (
    create_lesson_cards_for_database,
)

logger = logging.getLogger(__name__)


def create_tables_if_not_exist(conn: sqlite3.Connection):
    """Create lesson-related tables if they don't exist."""

    # Create the proper card_summaries table that the database service expects
    conn.execute("""
        CREATE TABLE IF NOT EXISTS card_summaries (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            tags_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            modified_at TEXT NOT NULL,
            has_attachments BOOLEAN DEFAULT FALSE
        )
    """)

    # Extended cards table for lesson metadata (backward compatibility)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT,
            tags TEXT,  -- JSON array of tag names
            card_type TEXT DEFAULT 'standard',
            lesson_metadata TEXT,  -- JSON for lesson-specific data
            created_at TEXT,
            modified_at TEXT
        )
    """)

    # Tags table (normalized)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    # Card-Tag relations
    conn.execute("""
        CREATE TABLE IF NOT EXISTS card_tags (
            card_id TEXT NOT NULL,
            tag_id INTEGER NOT NULL,
            FOREIGN KEY (card_id) REFERENCES card_summaries(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id),
            PRIMARY KEY (card_id, tag_id)
        )
    """)

    # Lesson state table for tracking user progress
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lesson_state (
            user_id TEXT DEFAULT 'default',
            lesson_state_json TEXT,
            updated_at TEXT,
            PRIMARY KEY (user_id)
        )
    """)

    conn.commit()


def populate_lesson_cards(conn: sqlite3.Connection):
    """Populate database with lesson cards."""
    logger.info("Populating lesson cards...")

    # Get all available lessons (except production)
    available_lessons = [1, 2, 3, 4, 5, 6, 7]

    total_cards = 0
    for lesson_num in available_lessons:
        lesson_cards = create_lesson_cards_for_database(lesson_num)

        for card_data in lesson_cards:
            # Convert lesson_metadata to JSON string
            lesson_metadata_json = json.dumps(card_data['lesson_metadata'])
            tags_json = json.dumps(card_data['tags'])

            # Insert into both tables
            # 1. Extended cards table for lesson metadata
            conn.execute("""
                INSERT OR REPLACE INTO cards
                (id, title, content, tags, card_type, lesson_metadata, created_at, modified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                card_data['id'],
                card_data['title'],
                card_data['content'],
                tags_json,
                card_data['card_type'],
                lesson_metadata_json,
                card_data['created_at'],
                card_data['modified_at']
            ))

            # 2. Card summaries table for the database service
            conn.execute("""
                INSERT OR REPLACE INTO card_summaries
                (id, title, tags_json, created_at, modified_at, has_attachments)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                card_data['id'],
                card_data['title'],
                tags_json,
                card_data['created_at'],
                card_data['modified_at'],
                False  # no attachments for lesson cards
            ))

            # 3. Populate normalized tags and relations
            for tag in card_data['tags']:
                # Insert tag if not exists
                conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))

                # Get tag ID
                tag_id = conn.execute("SELECT id FROM tags WHERE name = ?", (tag,)).fetchone()[0]

                # Insert card-tag relation
                conn.execute("""
                    INSERT OR IGNORE INTO card_tags (card_id, tag_id) VALUES (?, ?)
                """, (card_data['id'], tag_id))

            total_cards += 1

    conn.commit()
    logger.info(f"Inserted {total_cards} lesson cards")


def populate_lesson_tags(conn: sqlite3.Connection):
    """Tags are now populated as part of card population - this function maintained for compatibility."""
    logger.info("Lesson tags populated via card insertion")


def initialize_default_lesson_state(conn: sqlite3.Connection):
    """Initialize default lesson state for the default user."""
    logger.info("Initializing default lesson state...")

    default_state = get_default_lesson_state()
    state_json = json.dumps(default_state)

    conn.execute("""
        INSERT OR REPLACE INTO lesson_state
        (user_id, lesson_state_json, updated_at)
        VALUES (?, ?, ?)
    """, (
        'default',
        state_json,
        datetime.now(UTC).isoformat()
    ))

    conn.commit()
    logger.info("Default lesson state initialized")


def main():
    """Main population function."""
    logging.basicConfig(level=logging.INFO)

    # Database path (tutorial database)
    db_path = Path("/var/data/tutorial_customer.db")

    logger.info(f"Populating lesson data in database: {db_path}")

    try:
        with sqlite3.connect(db_path) as conn:
            # Create tables if needed
            create_tables_if_not_exist(conn)

            # Populate lesson content
            populate_lesson_cards(conn)
            populate_lesson_tags(conn)

            # Initialize lesson state
            initialize_default_lesson_state(conn)

            logger.info("✅ Lesson database population completed successfully!")

            # Verify population
            card_count = conn.execute("SELECT COUNT(*) FROM cards WHERE card_type = 'lesson'").fetchone()[0]
            summary_count = conn.execute("SELECT COUNT(*) FROM card_summaries").fetchone()[0]
            tag_count = conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0]

            logger.info("📊 Database now contains:")
            logger.info(f"   - {card_count} lesson cards")
            logger.info(f"   - {summary_count} card summaries")
            logger.info(f"   - {tag_count} tags total")

    except Exception as e:
        logger.error(f"❌ Error populating lesson database: {e}")
        raise


if __name__ == "__main__":
    main()
