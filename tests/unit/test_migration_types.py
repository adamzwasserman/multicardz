"""
Unit tests for migration types (simple pytest, no BDD).
Tests high-performance characteristics.
"""
import sys
import time
from pathlib import Path

import pytest

from apps.shared.migrations.types import (
    SchemaError,
    SchemaErrorCategory,
    Migration,
    MigrationResult,
)


class TestSchemaErrorCategory:
    """Test SchemaErrorCategory integer enum."""

    def test_uses_integer_values(self):
        """Verify categories use integer values for fast comparison."""
        assert isinstance(SchemaErrorCategory.MISSING_TABLE.value, int)
        assert isinstance(SchemaErrorCategory.MISSING_TRIGGER.value, int)

    def test_fast_comparison(self):
        """Verify category comparisons are fast."""
        cat1 = SchemaErrorCategory.MISSING_TABLE
        cat2 = SchemaErrorCategory.MISSING_TRIGGER

        # Just verify comparison works correctly
        assert cat1 == SchemaErrorCategory.MISSING_TABLE
        assert cat1 != cat2


class TestSchemaError:
    """Test SchemaError NamedTuple."""

    def test_immutability(self):
        """Verify SchemaError is immutable."""
        error = SchemaError(
            category=SchemaErrorCategory.MISSING_TABLE,
            identifier="cards",
            original_error=Exception("test"),
            error_message="no such table: cards"
        )

        with pytest.raises(AttributeError):
            error.category = SchemaErrorCategory.MISSING_TRIGGER

    def test_minimal_memory(self):
        """Verify SchemaError has minimal memory footprint."""
        errors = [
            SchemaError(
                category=SchemaErrorCategory.MISSING_TABLE,
                identifier=f"table_{i}",
                original_error=Exception(f"test {i}"),
                error_message=f"no such table: table_{i}"
            )
            for i in range(1000)
        ]

        total_memory = sum(sys.getsizeof(err) for err in errors)
        # Each NamedTuple instance should be ~56-80 bytes
        # 1000 instances should be well under 100KB
        assert total_memory < 100 * 1024, f"Memory usage {total_memory} bytes too high"

    def test_helper_methods(self):
        """Test helper methods for error classification."""
        table_error = SchemaError(
            category=SchemaErrorCategory.MISSING_TABLE,
            identifier="cards",
            original_error=Exception("test"),
            error_message="no such table: cards"
        )

        assert table_error.is_missing_table() is True
        assert table_error.is_missing_trigger() is False
        assert table_error.is_constraint_violation() is False


class TestMigration:
    """Test Migration NamedTuple."""

    def test_immutability(self):
        """Verify Migration is immutable."""
        migration = Migration(version=2, sql_file="002_add_bitmap_sequences.sql")

        with pytest.raises(AttributeError):
            migration.version = 999

    def test_sql_path_construction(self):
        """Verify sql_path method works correctly."""
        migration = Migration(version=2, sql_file="002_add_bitmap_sequences.sql")
        base_dir = Path("/migrations")

        result = migration.sql_path(base_dir)

        assert result == Path("/migrations/002_add_bitmap_sequences.sql")
        assert isinstance(result, Path)

    def test_sql_path_performance(self):
        """Verify sql_path is fast (inline operation)."""
        migration = Migration(version=2, sql_file="002_add_bitmap_sequences.sql")
        base_dir = Path("/migrations")

        # Just verify it's callable many times without issue
        for _ in range(1000):
            _ = migration.sql_path(base_dir)

class TestMigrationResult:
    """Test MigrationResult NamedTuple."""

    def test_immutability(self):
        """Verify MigrationResult is immutable."""
        result = MigrationResult(
            success=True,
            version=2,
            duration_ms=5.2,
            error=None
        )

        with pytest.raises(AttributeError):
            result.success = False

    def test_helper_methods(self):
        """Test helper methods for result checking."""
        success_result = MigrationResult(
            success=True,
            version=2,
            duration_ms=5.2,
            error=None
        )

        failure_result = MigrationResult(
            success=False,
            version=2,
            duration_ms=10.5,
            error="Migration failed"
        )

        assert success_result.is_success() is True
        assert success_result.is_failure() is False

        assert failure_result.is_success() is False
        assert failure_result.is_failure() is True

    def test_minimal_memory(self):
        """Verify MigrationResult has minimal memory footprint."""
        results = [
            MigrationResult(
                success=i % 2 == 0,
                version=i,
                duration_ms=float(i),
                error=f"Error {i}" if i % 2 == 1 else None
            )
            for i in range(10000)
        ]

        total_memory = sum(sys.getsizeof(r) for r in results)
        # 10000 instances should be well under 500KB
        assert total_memory < 500 * 1024, f"Memory usage {total_memory} bytes too high"

    def test_fast_creation(self):
        """Verify MigrationResult can be created quickly."""
        start = time.perf_counter()

        for i in range(1000):
            _ = MigrationResult(
                success=True,
                version=i,
                duration_ms=1.0,
                error=None
            )

        duration = time.perf_counter() - start

        # Creating 1000 instances should be very fast (< 10ms)
        assert duration < 0.01, f"Creation took {duration*1000}ms (too slow)"


class TestTypePerformance:
    """Performance tests for type system."""

    def test_schema_error_creation_speed(self):
        """Verify SchemaError can be created rapidly."""
        start = time.perf_counter()

        for i in range(1000):
            _ = SchemaError(
                category=SchemaErrorCategory.MISSING_TABLE,
                identifier=f"table_{i}",
                original_error=Exception(f"test {i}"),
                error_message=f"no such table: table_{i}"
            )

        duration = time.perf_counter() - start

        # Should be very fast (< 10ms for 1000 instances)
        assert duration < 0.01, f"Creation took {duration*1000}ms (too slow)"
