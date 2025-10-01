#!/usr/bin/env python3
"""
Script to sync lesson data from Python definitions to SQLite database.
This creates the read-only lesson database that will be shared with all users.
"""

import sqlite3
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import lesson data
from apps.shared.data.onboarding_lessons import (
    ALL_LESSON_CARDS,
    ALL_LESSON_TAGS,
    LESSON_PROGRESSION
)

def sync_lessons_to_database(db_path="/var/data/multicardz_dev.db"):
    """Sync all lesson data to the database."""

    print(f"🔄 Syncing lesson data to {db_path}")

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Clear existing lesson data
        print("🗑️  Clearing existing lesson data...")
        cursor.execute("DELETE FROM cards WHERE card_type = 'lesson'")
        cursor.execute("DELETE FROM card_summaries WHERE id LIKE 'lesson%'")

        # Insert lesson cards
        print(f"📝 Inserting {len(ALL_LESSON_CARDS)} lesson cards...")

        for card in ALL_LESSON_CARDS:
            # Insert into cards table
            cursor.execute("""
                INSERT OR REPLACE INTO cards (
                    id, title, content, card_type, lesson_metadata,
                    created_at, modified_at
                ) VALUES (?, ?, ?, 'lesson', ?, ?, ?)
            """, (
                card.id,
                card.title,
                card.content,
                json.dumps({
                    'lesson_number': card.lesson_number,
                    'step_number': card.step_number,
                    'success_criteria': card.success_criteria,
                    'next_action': card.next_action
                }),
                datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat()
            ))

            # Insert into card_summaries table
            cursor.execute("""
                INSERT OR REPLACE INTO card_summaries (
                    id, title, tags_json, created_at, modified_at, has_attachments
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                card.id,
                card.title,
                json.dumps(card.tags),
                datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat(),
                False
            ))

            print(f"  ✅ {card.id}: {card.title}")

        # Insert lesson tags (for reference, though tags are loaded from Python)
        print(f"🏷️  Lesson tags available: {len(ALL_LESSON_TAGS)}")
        for tag in ALL_LESSON_TAGS:
            print(f"  🏷️  Lesson {tag.lesson_number}: {tag.name} → {tag.zone_target}")

        conn.commit()
        print("✅ Lesson sync complete!")

        # Verify the sync
        cursor.execute("SELECT COUNT(*) FROM cards WHERE card_type = 'lesson'")
        card_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM card_summaries WHERE id LIKE 'lesson%'")
        summary_count = cursor.fetchone()[0]

        print(f"📊 Database now contains:")
        print(f"   • {card_count} lesson cards")
        print(f"   • {summary_count} lesson card summaries")

        # Show lesson breakdown
        for lesson_num in [1, 2, 3]:
            cursor.execute("""
                SELECT COUNT(*) FROM cards
                WHERE card_type = 'lesson'
                AND JSON_EXTRACT(lesson_metadata, '$.lesson_number') = ?
            """, (lesson_num,))
            count = cursor.fetchone()[0]
            print(f"   • Lesson {lesson_num}: {count} cards")

if __name__ == "__main__":
    sync_lessons_to_database()