#!/usr/bin/env python
"""
One-time migration script to populate landing page content.

Usage:
    uv run python apps/public/scripts/run_migration.py
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Add apps/public to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import get_database_url
from services.content_migration import migrate_content_to_database


def check_existing_content(db: Session) -> int:
    """
    Check if content already migrated.

    Args:
        db: Database session

    Returns:
        count of existing landing pages
    """
    result = db.execute(text("SELECT COUNT(*) FROM landing_pages")).fetchone()
    count = result[0] if result else 0
    return count


def main():
    """Execute migration."""
    print("🚀 Starting landing page content migration...")

    # Database connection
    engine = create_engine(get_database_url())
    db = Session(bind=engine)

    try:
        # Check if already migrated
        existing_count = check_existing_content(db)
        if existing_count > 0:
            print(f"⚠️  {existing_count} landing pages already exist in database.")
            response = input("Continue anyway? This may create duplicates. (y/N): ")
            if response.lower() != 'y':
                print("Migration aborted.")
                return 0

        # HTML file path
        html_file = Path("/Users/adam/Downloads/landing-variations-viewer-v3.html")

        if not html_file.exists():
            print(f"❌ Error: HTML file not found at {html_file}")
            sys.exit(1)

        # Run migration
        print(f"📄 Parsing {html_file.name}...")
        count = migrate_content_to_database(html_file, db)

        print(f"✅ Successfully migrated {count} landing pages!")

        # Verification
        result = db.execute(text("""
            SELECT lp.slug, COUNT(lps.id) as section_count
            FROM landing_pages lp
            LEFT JOIN landing_page_sections lps ON lps.landing_page_id = lp.id
            GROUP BY lp.slug
            ORDER BY lp.slug
        """)).fetchall()

        print("\n📊 Migration Summary:")
        for row in result:
            print(f"  - {row[0]}: {row[1]} sections")

        return count

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    count = main()
    sys.exit(0 if count > 0 else 1)
