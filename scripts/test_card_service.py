#!/usr/bin/env python3
"""
Test card service with real database data.
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.shared.services.card_service import (
    create_database_config,
    with_db_session,
    get_all_card_summaries,
    create_card,
    filter_cards_with_operations_streamed,
    get_tag_statistics,
)


def test_card_service():
    """Test the card service with real database."""
    print("Testing MultiCardz card service with real database...")

    # Database configuration
    db_path = Path("/var/data/multicardz_dev.db")
    config = create_database_config(db_path)

    with with_db_session(config) as conn:

        # Test 1: Load all cards
        print("\n1. Testing card loading...")
        try:
            cards = get_all_card_summaries(conn)
            print(f"✅ Loaded {len(cards)} cards from database")

            # Show first few cards
            for i, card in enumerate(list(cards)[:3]):
                print(f"   Card {i+1}: {card.title} (tags: {len(card.tags)})")

        except Exception as e:
            print(f"❌ Card loading failed: {e}")
            return False

        # Test 2: Get tag statistics
        print("\n2. Testing tag statistics...")
        try:
            tag_stats = get_tag_statistics(conn)
            print(f"✅ Found {len(tag_stats)} unique tags")

            # Show most common tags
            sorted_tags = sorted(tag_stats, key=lambda x: x[1], reverse=True)[:5]
            print("   Most common tags:")
            for tag, count in sorted_tags:
                print(f"     {tag}: {count} cards")

        except Exception as e:
            print(f"❌ Tag statistics failed: {e}")
            return False

        # Test 3: Create a new card
        print("\n3. Testing card creation...")
        try:
            new_card_id = create_card(
                conn,
                title="Test Card from Service",
                content="This is a test card created through the card service.",
                tags=frozenset(["test", "service", "python"])
            )
            print(f"✅ Created new card: {new_card_id}")

        except Exception as e:
            print(f"❌ Card creation failed: {e}")
            return False

        # Test 4: Filter cards by tags
        print("\n4. Testing card filtering...")
        try:
            # Filter for cards with 'python' tag
            operations = [("intersection", [("python", 1)])]
            result = filter_cards_with_operations_streamed(
                conn, operations, use_cache=False
            )

            print(f"✅ Found {len(result.cards)} cards with 'python' tag")
            print(f"   Execution time: {result.execution_time_ms:.2f}ms")

            # Show filtered cards
            for card in list(result.cards)[:3]:
                print(f"     {card.title} (tags: {sorted(card.tags)})")

        except Exception as e:
            print(f"❌ Card filtering failed: {e}")
            return False

        # Test 5: Union operation
        print("\n5. Testing union operation...")
        try:
            # Get cards with either 'python' OR 'javascript' tags
            operations = [("union", [("python", 1), ("javascript", 1)])]
            result = filter_cards_with_operations_streamed(
                conn, operations, use_cache=False
            )

            print(f"✅ Found {len(result.cards)} cards with 'python' OR 'javascript' tags")
            print(f"   Execution time: {result.execution_time_ms:.2f}ms")

        except Exception as e:
            print(f"❌ Union operation failed: {e}")
            return False

        # Test 6: Complex operations
        print("\n6. Testing complex operations...")
        try:
            # Get cards with 'python' AND ('api' OR 'web-development')
            operations = [
                ("intersection", [("python", 1)]),
                ("union", [("api", 1), ("web-development", 1)])
            ]
            result = filter_cards_with_operations_streamed(
                conn, operations, use_cache=False
            )

            print(f"✅ Complex operation returned {len(result.cards)} cards")
            print(f"   Execution time: {result.execution_time_ms:.2f}ms")

        except Exception as e:
            print(f"❌ Complex operations failed: {e}")
            return False

        print("\n✅ All card service tests passed!")
        return True


if __name__ == "__main__":
    success = test_card_service()
    exit(0 if success else 1)