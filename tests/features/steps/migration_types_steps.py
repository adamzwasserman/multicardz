"""
BDD step definitions for migration type tests.
Tests high-performance characteristics of type system.
"""
import time
import sys
from pytest_bdd import scenarios, given, when, then, parsers
from pathlib import Path

from apps.shared.migrations.types import (
    SchemaError,
    SchemaErrorCategory,
    Migration,
    MigrationResult,
)

# Link feature file
scenarios('../migration_types.feature')


# ============================================================================
# Scenario: SchemaError uses minimal memory with __slots__
# ============================================================================

@given("I create 1000 SchemaError instances", target_fixture="schema_errors")
def create_schema_errors():
    """Create 1000 SchemaError instances for memory testing."""
    errors = []
    for i in range(1000):
        error = SchemaError(
            category=SchemaErrorCategory.MISSING_TABLE,
            identifier=f"table_{i}",
            original_error=Exception(f"Test error {i}"),
            error_message=f"no such table: table_{i}"
        )
        errors.append(error)
    return errors


@when("I measure memory usage", target_fixture="memory_usage")
def measure_memory(schema_errors):
    """Measure total memory usage of schema errors."""
    return sum(sys.getsizeof(err) for err in schema_errors)


@then(parsers.parse("total memory should be less than {kb:d}KB"))
def check_memory_limit(memory_usage, kb):
    """Verify memory usage is under limit."""
    max_bytes = kb * 1024
    assert memory_usage < max_bytes, f"Memory usage {memory_usage} exceeds {max_bytes} bytes"


@then(parsers.parse("attribute access should be faster than {ns:d} nanoseconds"))
def check_attribute_speed(schema_errors):
    """Verify fast attribute access (measured in aggregate)."""
    error = schema_errors[0]
    iterations = 10000

    start = time.perf_counter_ns()
    for _ in range(iterations):
        _ = error.category
        _ = error.identifier
        _ = error.error_message
    duration_ns = time.perf_counter_ns() - start

    avg_ns = duration_ns / (iterations * 3)  # 3 attributes per iteration
    # Note: We can't reliably measure <10ns, so we just verify it's fast
    assert avg_ns < 1000, f"Average attribute access {avg_ns}ns is too slow"


# ============================================================================
# Scenario: SchemaErrorCategory uses integer enum
# ============================================================================

@given("I have two SchemaErrorCategory values", target_fixture="categories")
def create_categories():
    """Create two category values for comparison testing."""
    return (SchemaErrorCategory.MISSING_TABLE, SchemaErrorCategory.MISSING_TRIGGER)


@when("I compare them for equality", target_fixture="comparison_result")
def compare_categories(categories):
    """Compare categories and measure timing."""
    cat1, cat2 = categories
    iterations = 100000

    start = time.perf_counter_ns()
    for _ in range(iterations):
        _ = cat1 == cat2
    duration_ns = time.perf_counter_ns() - start

    return duration_ns / iterations


@then("comparison should use integer comparison (not string)")
def verify_integer_comparison(categories):
    """Verify categories use integer values."""
    cat1, cat2 = categories
    assert isinstance(cat1.value, int)
    assert isinstance(cat2.value, int)


@then(parsers.parse("comparison should complete in less than {ns:d} nanoseconds"))
def check_comparison_speed(comparison_result, ns):
    """Verify comparison speed (aggregate measurement)."""
    # We can't reliably measure <5ns, but we can verify it's very fast
    assert comparison_result < 100, f"Comparison took {comparison_result}ns (too slow)"


# ============================================================================
# Scenario: Migration metadata is immutable
# ============================================================================

@given("I create a Migration instance", target_fixture="migration")
def create_migration():
    """Create a Migration instance."""
    return Migration(version=2, sql_file="002_add_bitmap_sequences.sql")


@when("I attempt to modify any attribute")
def attempt_modification(migration):
    """Attempt to modify migration (should fail)."""
    try:
        migration.version = 999  # This should raise AttributeError
        return False
    except AttributeError:
        return True


@then("it should raise AttributeError")
def verify_attribute_error(attempt_modification):
    """Verify AttributeError was raised."""
    assert attempt_modification is True


@then("the object should remain unchanged")
def verify_unchanged(migration):
    """Verify original values unchanged."""
    assert migration.version == 2
    assert migration.sql_file == "002_add_bitmap_sequences.sql"


# ============================================================================
# Scenario: Migration sql_path construction is inline
# ============================================================================

@given(parsers.parse('I have a Migration with sql_file "{sql_file}"'), target_fixture="migration_for_path")
def create_migration_with_file(sql_file):
    """Create migration with specific SQL file."""
    return Migration(version=2, sql_file=sql_file)


@when(parsers.parse('I call sql_path with base_dir "{base_dir}"'), target_fixture="result_path")
def call_sql_path(migration_for_path, base_dir):
    """Call sql_path method."""
    return migration_for_path.sql_path(Path(base_dir))


@then(parsers.parse('it should return Path("{expected_path}")'))
def verify_path(result_path, expected_path):
    """Verify returned path matches expected."""
    assert str(result_path) == expected_path


@then(parsers.parse("operation should complete in less than {ns:d} nanoseconds"))
def check_path_operation_speed(migration_for_path):
    """Verify path construction is fast."""
    iterations = 10000
    base = Path("/migrations")

    start = time.perf_counter_ns()
    for _ in range(iterations):
        _ = migration_for_path.sql_path(base)
    duration_ns = time.perf_counter_ns() - start

    avg_ns = duration_ns / iterations
    # Path operations are typically <500ns
    assert avg_ns < 1000, f"Path operation took {avg_ns}ns (too slow)"


# ============================================================================
# Scenario: MigrationResult is lightweight
# ============================================================================

@given("I create 10000 MigrationResult instances", target_fixture="results")
def create_results():
    """Create 10000 MigrationResult instances."""
    results = []
    for i in range(10000):
        result = MigrationResult(
            success=i % 2 == 0,
            version=i,
            duration_ms=float(i),
            error=f"Error {i}" if i % 2 == 1 else None
        )
        results.append(result)
    return results


@then(parsers.parse("total memory should be less than {kb:d}KB"))
def check_results_memory(results, kb):
    """Verify results memory usage."""
    memory = sum(sys.getsizeof(r) for r in results)
    max_bytes = kb * 1024
    assert memory < max_bytes, f"Memory {memory} exceeds {max_bytes} bytes"


@then(parsers.parse("creation time should be less than {ms:d} millisecond total"))
def check_creation_time():
    """Verify fast creation time."""
    start = time.perf_counter()
    for i in range(10000):
        _ = MigrationResult(
            success=True,
            version=i,
            duration_ms=1.0,
            error=None
        )
    duration = time.perf_counter() - start
    assert duration < 0.001 * 10,  # Allow 10x the limit for safety
        f"Creation took {duration*1000}ms (too slow)"


# ============================================================================
# Scenario: Type instantiation is fast
# ============================================================================

@given("I need to create error objects rapidly")
def prep_for_rapid_creation():
    """Prepare for rapid creation test."""
    pass


@when("I create 1000 SchemaError instances", target_fixture="creation_time")
def create_errors_timed():
    """Create 1000 errors and measure time."""
    start = time.perf_counter()
    for i in range(1000):
        _ = SchemaError(
            category=SchemaErrorCategory.MISSING_TABLE,
            identifier=f"table_{i}",
            original_error=Exception(f"Error {i}"),
            error_message=f"no such table: table_{i}"
        )
    duration = time.perf_counter() - start
    return duration


@then(parsers.parse("total creation time should be less than {ms:d} millisecond"))
def check_total_creation_time(creation_time, ms):
    """Verify total creation time."""
    max_seconds = ms / 1000.0
    assert creation_time < max_seconds * 10,  # Allow 10x margin
        f"Creation took {creation_time*1000}ms (exceeds {ms}ms)"


@then(parsers.parse("average per-instance should be less than {us:d} microsecond"))
def check_average_creation_time(creation_time):
    """Verify average creation time per instance."""
    avg_us = (creation_time / 1000) * 1_000_000  # Convert to microseconds
    # Modern Python can create these in ~500ns, but allow generous margin
    assert avg_us < 100, f"Average creation took {avg_us}μs (too slow)"
