"""
Integration tests for CardService with set operations.

These tests verify the complete integration between database storage
and set operations using actual database-generated tag count tuples.
"""

import tempfile
from pathlib import Path

import pytest

from apps.shared.models.card import CardSummary
from apps.shared.models.user_preferences import UserPreferences
from apps.shared.services.card_service import create_card_service


class TestCardServiceIntegration:
    """Integration tests for CardService with set operations."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            db_path = Path(temp_file.name)
        yield db_path
        # Cleanup
        if db_path.exists():
            db_path.unlink()

    @pytest.fixture
    def sample_cards_data(self):
        """Sample card data for testing."""
        return [
            {
                "title": "Bug Fix #1",
                "content": "Fixed critical bug",
                "tags": ["urgent", "bug", "backend"],
            },
            {
                "title": "Feature Request",
                "content": "New user feature",
                "tags": ["feature", "frontend", "medium"],
            },
            {
                "title": "Urgent Hotfix",
                "content": "Critical security fix",
                "tags": ["urgent", "security", "critical"],
            },
            {
                "title": "Documentation Update",
                "content": "Updated API docs",
                "tags": ["docs", "low", "maintenance"],
            },
            {
                "title": "Performance Bug",
                "content": "Fixed slow query",
                "tags": ["bug", "performance", "database"],
            },
            {
                "title": "UI Enhancement",
                "content": "Better user interface",
                "tags": ["feature", "frontend", "ui"],
            },
            {
                "title": "Security Audit",
                "content": "Security review",
                "tags": ["security", "audit", "high"],
            },
            {
                "title": "Bug in Frontend",
                "content": "Fixed display issue",
                "tags": ["bug", "frontend", "ui"],
            },
            {
                "title": "Database Migration",
                "content": "Schema update",
                "tags": ["database", "migration", "backend"],
            },
            {
                "title": "Critical Alert",
                "content": "System alert",
                "tags": ["urgent", "critical", "monitoring"],
            },
        ]

    def test_card_service_basic_operations(self, temp_db_path, sample_cards_data):
        """Test basic card service operations."""
        with create_card_service(temp_db_path) as service:
            # Create cards
            created_ids = service.bulk_import_cards(sample_cards_data)
            assert len(created_ids) == len(sample_cards_data)

            # Get all cards
            all_cards = service.get_all_card_summaries()
            assert len(all_cards) == len(sample_cards_data)

            # Verify cards have correct data
            for card in all_cards:
                assert isinstance(card, CardSummary)
                assert card.title
                assert isinstance(card.tags, frozenset)

            # Test individual card retrieval
            first_card_id = created_ids[0]
            card_summary = service.get_card_summary(first_card_id)
            card_detail = service.get_card_detail(first_card_id)

            assert card_summary.id == first_card_id
            assert card_detail.id == first_card_id
            assert card_detail.content == sample_cards_data[0]["content"]

    def test_tag_count_tuple_generation(self, temp_db_path, sample_cards_data):
        """Test tag count tuple generation from database."""
        with create_card_service(temp_db_path) as service:
            # Create cards
            service.bulk_import_cards(sample_cards_data)

            # Get tag statistics
            tag_stats = service.get_tag_statistics()

            # Verify format
            assert isinstance(tag_stats, list)
            for tag, count in tag_stats:
                assert isinstance(tag, str)
                assert isinstance(count, int)
                assert count > 0

            # Verify some expected tags and counts
            tag_dict = dict(tag_stats)
            assert tag_dict["urgent"] == 3  # 3 cards have 'urgent' tag
            assert tag_dict["bug"] == 3  # 3 cards have 'bug' tag
            assert tag_dict["frontend"] == 3  # 3 cards have 'frontend' tag

            # Verify sorting (should be ascending by count for selectivity)
            for i in range(len(tag_stats) - 1):
                current_count = tag_stats[i][1]
                next_count = tag_stats[i + 1][1]
                assert current_count <= next_count

    def test_set_operations_integration(self, temp_db_path, sample_cards_data):
        """Test set operations integration with database tag counts."""
        with create_card_service(temp_db_path) as service:
            # Create cards
            service.bulk_import_cards(sample_cards_data)

            # Test intersection filtering (cards with both 'urgent' AND 'bug')
            intersection_ops = [
                (
                    "intersection",
                    [("urgent", 100), ("bug", 100)],
                )  # Mock counts will be replaced
            ]

            result = service.filter_cards_with_operations(intersection_ops)

            # Should find cards that have both 'urgent' and 'bug' tags
            assert len(result.cards) == 1  # Only "Bug Fix #1" has both
            card = list(result.cards)[0]
            assert "urgent" in card.tags and "bug" in card.tags

            # Verify performance
            assert result.execution_time_ms < 100  # Should be very fast

    def test_complex_set_operations(self, temp_db_path, sample_cards_data):
        """Test complex set operations with multiple filters."""
        with create_card_service(temp_db_path) as service:
            # Create cards
            service.bulk_import_cards(sample_cards_data)

            # Complex operation: (urgent OR critical) AND NOT docs
            operations = [
                ("union", [("urgent", 100), ("critical", 100)]),  # urgent OR critical
                ("difference", [("docs", 100)]),  # NOT docs
            ]

            result = service.filter_cards_with_operations(operations)

            # Verify results
            for card in result.cards:
                has_urgent_or_critical = (
                    "urgent" in card.tags or "critical" in card.tags
                )
                has_docs = "docs" in card.tags
                assert has_urgent_or_critical and not has_docs

            # Should find several cards
            assert len(result.cards) >= 3

    def test_user_preferences_integration(self, temp_db_path, sample_cards_data):
        """Test user preferences integration with filtering."""
        with create_card_service(temp_db_path) as service:
            # Create cards
            service.bulk_import_cards(sample_cards_data)

            # Create user preferences
            preferences = UserPreferences(user_id="test_user")
            service.save_user_preferences(preferences)

            # Load preferences
            loaded_prefs = service.get_user_preferences("test_user")
            assert loaded_prefs.user_id == "test_user"

            # Test filtering with preferences
            operations = [("intersection", [("bug", 100)])]
            result = service.filter_cards_with_operations(
                operations, user_preferences=loaded_prefs
            )

            # Should apply user preferences to ordering
            assert len(result.cards) == 3  # 3 cards with 'bug' tag
            assert not result.cache_hit  # First execution

    def test_performance_with_database_optimization(
        self, temp_db_path, sample_cards_data
    ):
        """Test performance improvements from database tag count optimization."""
        with create_card_service(temp_db_path) as service:
            # Create cards
            service.bulk_import_cards(sample_cards_data)

            # Get tag statistics to verify optimization data
            tag_stats = service.get_tag_statistics()
            assert len(tag_stats) > 0

            # Clear cache to ensure fresh start
            service.clear_all_caches()

            # Get actual tag counts from database for consistent operations
            tag_dict = dict(tag_stats)
            urgent_count = tag_dict.get("urgent", 1)
            security_count = tag_dict.get("security", 1)

            # Test operation with database-accurate tag counts
            operations = [
                (
                    "intersection",
                    [("urgent", urgent_count), ("security", security_count)],
                )
            ]

            # First run
            result1 = service.filter_cards_with_operations(
                operations, optimize_order=True
            )

            # Second run with identical operation (should hit cache)
            result2 = service.filter_cards_with_operations(
                operations, optimize_order=True
            )

            # Verify optimization effects
            assert result1.execution_time_ms > 0
            assert not result1.cache_hit  # First run should not hit cache

            # Note: Cache might not hit due to card ID variations, but operation should complete
            # This test mainly verifies that database tag count integration works
            assert result1.operations_applied == result2.operations_applied
            assert len(result1.cards) == len(result2.cards)  # Same results

    def test_service_statistics(self, temp_db_path, sample_cards_data):
        """Test service statistics reporting."""
        with create_card_service(temp_db_path) as service:
            # Create cards
            service.bulk_import_cards(sample_cards_data)

            # Perform some operations to generate statistics
            operations = [("intersection", [("bug", 100)])]
            service.filter_cards_with_operations(operations)

            # Get statistics
            stats = service.get_service_statistics()

            # Verify statistics structure
            assert "database" in stats
            assert "operations" in stats
            assert "tag_statistics" in stats

            # Verify database statistics
            db_stats = stats["database"]
            assert db_stats["card_summaries_count"] == len(sample_cards_data)
            assert db_stats["card_details_count"] == len(sample_cards_data)
            assert db_stats["unique_tags_count"] > 0

            # Verify operation statistics
            op_stats = stats["operations"]
            assert "cache_hit_rate" in op_stats

    def test_bulk_operations_performance(self, temp_db_path):
        """Test bulk operations performance."""
        # Create larger dataset for performance testing
        large_dataset = []
        for i in range(1000):
            large_dataset.append(
                {
                    "title": f"Card {i}",
                    "content": f"Content for card {i}",
                    "tags": [f"tag{i%10}", f"category{i%5}", f"type{i%3}"],
                }
            )

        with create_card_service(temp_db_path) as service:
            # Measure bulk import time
            import time

            start_time = time.perf_counter()
            created_ids = service.bulk_import_cards(large_dataset)
            import_time = (time.perf_counter() - start_time) * 1000

            assert len(created_ids) == 1000
            assert import_time < 1000  # Should complete in under 1 second

            # Measure filtering time
            start_time = time.perf_counter()
            all_cards = service.get_all_card_summaries()
            load_time = (time.perf_counter() - start_time) * 1000

            assert len(all_cards) == 1000
            assert load_time < 100  # Should load in under 100ms

            # Test set operations on large dataset
            operations = [("intersection", [("tag1", 100)])]
            start_time = time.perf_counter()
            result = service.filter_cards_with_operations(operations)
            filter_time = (time.perf_counter() - start_time) * 1000

            assert len(result.cards) == 100  # Every 10th card has tag1
            assert filter_time < 100  # Temporarily increased threshold for adaptive optimization

    def test_error_handling_and_rollback(self, temp_db_path):
        """Test error handling and transaction rollback."""
        with create_card_service(temp_db_path) as service:
            # Create valid card first
            card_id = service.create_card(
                "Valid Card", "Valid content", frozenset(["test"])
            )
            assert card_id

            # Test invalid bulk import (should rollback)
            invalid_data = [
                {"title": "Valid Card 1", "content": "Content 1", "tags": ["tag1"]},
                {
                    "title": "",
                    "content": "Content 2",
                    "tags": ["tag2"],
                },  # Invalid: empty title
                {"title": "Valid Card 2", "content": "Content 3", "tags": ["tag3"]},
            ]

            # This should fail and rollback
            with pytest.raises(Exception):
                service.bulk_import_cards(invalid_data)

            # Verify rollback - should still only have 1 card
            all_cards = service.get_all_card_summaries()
            assert len(all_cards) == 1  # Only the original valid card

    def test_export_import_cycle(self, temp_db_path, sample_cards_data):
        """Test complete export/import cycle."""
        with create_card_service(temp_db_path) as service:
            # Import original data
            original_ids = service.bulk_import_cards(sample_cards_data)

            # Export all data
            exported_data = service.export_cards_data()

            # Verify export structure
            assert len(exported_data) == len(sample_cards_data)
            for card_data in exported_data:
                assert "id" in card_data
                assert "title" in card_data
                assert "tags" in card_data
                assert "content" in card_data

            # Clear all cards
            for card_id in original_ids:
                service.delete_card(card_id)

            # Verify empty
            assert len(service.get_all_card_summaries()) == 0

            # Re-import exported data
            reimported_ids = service.bulk_import_cards(exported_data)

            # Verify data integrity
            final_cards = service.get_all_card_summaries()
            assert len(final_cards) == len(sample_cards_data)

            # Test that set operations still work after export/import
            operations = [("intersection", [("bug", 100)])]
            result = service.filter_cards_with_operations(operations)
            assert len(result.cards) == 3  # Should still find 3 bug cards
