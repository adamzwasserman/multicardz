#!/usr/bin/env python3
"""
Test database fixture for Playwright tests.

Creates /tmp/test_multicardz.db with test data for spatial rendering tests.
"""

import json
import sqlite3
from pathlib import Path

import httpx

# Test database path - use default database for initial testing
TEST_DB_PATH = Path("/var/data/tutorial_customer.db")

# Server URL
SERVER_URL = "http://localhost:8011"


def create_test_database():
    """Create test database with schema."""
    # Remove existing test database
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    print(f"Creating test database: {TEST_DB_PATH}")

    # Create database connection
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()

    # Create schema (zero-trust architecture)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            card_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            tags TEXT,
            tag_bitmaps TEXT,
            user_id TEXT NOT NULL,
            workspace_id TEXT NOT NULL,
            created TEXT DEFAULT (datetime('now')),
            modified TEXT DEFAULT (datetime('now')),
            deleted TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            tag_id TEXT PRIMARY KEY,
            tag TEXT NOT NULL,
            card_count INTEGER DEFAULT 0,
            tag_bitmap INTEGER DEFAULT 0,
            user_id TEXT NOT NULL,
            workspace_id TEXT NOT NULL,
            created TEXT DEFAULT (datetime('now')),
            modified TEXT DEFAULT (datetime('now')),
            deleted TEXT
        )
    """)

    conn.commit()
    conn.close()

    print(f"✅ Test database created: {TEST_DB_PATH}")


def create_test_data_direct():
    """
    Create test data directly in database.

    Test Data:
    - Card 1: [union1]
    - Card 2: [union1, intersection1]
    - Card 3: [union2]
    - Card 4: [union2, column1]
    - Card 5: [union2, row1]
    """
    print("\n📝 Creating test tags...")

    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()

    tags_to_create = [
        ("union_tag_1", "union1"),
        ("intersection_tag_1", "intersection1"),
        ("union_tag_2", "union2"),
        ("column_tag_1", "column1"),
        ("row_tag_1", "row1"),
    ]

    tag_ids = {}

    for tag_id, tag_name in tags_to_create:
        cursor.execute("""
            INSERT INTO tags (tag_id, tag, card_count, user_id, workspace_id)
            VALUES (?, ?, 0, 'default-user', 'default-workspace')
        """, (tag_id, tag_name))
        tag_ids[tag_name] = tag_id
        print(f"  ✅ Created tag: {tag_name} ({tag_id})")

    conn.commit()

    print(f"\n📇 Creating test cards...")

    cards_to_create = [
        ("card_union1_only", "Card with union1 only", ["union1"]),
        ("card_union1_intersection1", "Card with union1 and intersection1", ["union1", "intersection1"]),
        ("card_union2_only", "Card with union2 only", ["union2"]),
        ("card_union2_column1", "Card with union2 and column1", ["union2", "column1"]),
        ("card_union2_row1", "Card with union2 and row1", ["union2", "row1"]),
    ]

    for card_id, card_name, tag_names in cards_to_create:
        # Convert tag names to tag IDs (comma-separated)
        card_tag_ids = [tag_ids[tag_name] for tag_name in tag_names if tag_name in tag_ids]
        tags_csv = ",".join(card_tag_ids)

        cursor.execute("""
            INSERT INTO cards (card_id, name, tags, user_id, workspace_id)
            VALUES (?, ?, ?, 'default-user', 'default-workspace')
        """, (card_id, card_name, tags_csv))

        print(f"  ✅ Created card: {card_name} with tags {tag_names}")

    conn.commit()

    # Update tag card counts (since triggers don't exist in test DB)
    print("\n🔧 Updating tag card counts...")

    for tag_id, tag_name in tags_to_create:
        # Count cards with this tag
        cursor.execute("""
            SELECT COUNT(*) FROM cards
            WHERE tags LIKE ? AND deleted IS NULL
        """, (f"%{tag_id}%",))
        count = cursor.fetchone()[0]

        # Update tag card_count
        cursor.execute("""
            UPDATE tags SET card_count = ? WHERE tag_id = ?
        """, (count, tag_id))

        print(f"  ✅ {tag_name}: {count} cards")

    conn.commit()
    conn.close()

    print("\n✅ Test data creation complete!")


def verify_test_database():
    """Verify test database has correct data."""
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()

    # Count tags
    cursor.execute("SELECT COUNT(*) FROM tags WHERE deleted IS NULL")
    tag_count = cursor.fetchone()[0]

    # Count cards
    cursor.execute("SELECT COUNT(*) FROM cards WHERE deleted IS NULL")
    card_count = cursor.fetchone()[0]

    print(f"\n📊 Test Database Summary:")
    print(f"  Tags: {tag_count}")
    print(f"  Cards: {card_count}")

    # List all cards with their tags
    cursor.execute("""
        SELECT c.name, c.tags
        FROM cards c
        WHERE c.deleted IS NULL
    """)

    print(f"\n  Cards:")
    for card_name, tag_ids_csv in cursor.fetchall():
        if tag_ids_csv:
            # Lookup tag names
            tag_id_list = tag_ids_csv.split(",")
            placeholders = ",".join("?" * len(tag_id_list))
            cursor.execute(f"SELECT tag FROM tags WHERE tag_id IN ({placeholders})", tag_id_list)
            tag_names = [row[0] for row in cursor.fetchall()]
            print(f"    {card_name}: {tag_names}")
        else:
            print(f"    {card_name}: []")

    conn.close()

    return tag_count == 5 and card_count == 5


def main():
    """Main setup function."""
    print("🔧 Setting up test database for Playwright tests")
    print("=" * 60)

    # Step 1: Create database
    create_test_database()

    # Step 2: Create test data directly in database
    create_test_data_direct()

    # Step 3: Verify
    success = verify_test_database()

    if success:
        print(f"\n✅ Test database ready at: {TEST_DB_PATH}")
        print(f"   Use in Playwright tests with: databasePath: '{TEST_DB_PATH}'")
        return True
    else:
        print("\n❌ Test database verification failed!")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
