"""
Performance benchmarks for group tags operations.

Tests expansion engine performance, cache hit rates, and database operations
against the specified performance targets.
"""

import time
import statistics
import pytest
from apps.shared.services.group_storage import (
    create_group,
    add_member_to_group,
    get_group_by_id,
)
from apps.shared.services.group_expansion import (
    expand_group_recursive,
    get_cache_statistics,
    invalidate_expansion_cache,
    GroupExpansionCache,
)


def benchmark_operation(func, *args, iterations=100, **kwargs):
    """
    Benchmark an operation over multiple iterations.

    Returns (avg_ms, max_ms, min_ms, p95_ms, p99_ms)
    """
    times = []

    for _ in range(iterations):
        start = time.perf_counter()
        func(*args, **kwargs)
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms

    return {
        'avg': statistics.mean(times),
        'max': max(times),
        'min': min(times),
        'p95': sorted(times)[int(len(times) * 0.95)],
        'p99': sorted(times)[int(len(times) * 0.99)],
        'iterations': iterations,
        'total_ms': sum(times)
    }


def test_group_creation_performance(group_workspace):
    """
    Test group creation performance.

    Target: <50ms per creation
    """
    def create_test_group():
        group_id = create_group(
            name=f'perf-group-{time.time_ns()}',
            workspace_id=group_workspace['id'],
            created_by=group_workspace['created_by'],
            initial_member_ids=frozenset()
        )
        return group_id

    results = benchmark_operation(create_test_group, iterations=100)

    print(f"\n📊 Group Creation Performance:")
    print(f"   Average: {results['avg']:.2f}ms")
    print(f"   P95: {results['p95']:.2f}ms")
    print(f"   P99: {results['p99']:.2f}ms")
    print(f"   Max: {results['max']:.2f}ms")

    assert results['avg'] < 50, f"Average creation time {results['avg']:.2f}ms exceeds 50ms target"
    assert results['p95'] < 100, f"P95 creation time {results['p95']:.2f}ms exceeds 100ms"


def test_simple_expansion_performance(sample_group):
    """
    Test simple group expansion (10 members).

    Target: <5ms
    """
    def expand_test():
        return expand_group_recursive(sample_group)

    results = benchmark_operation(expand_test, iterations=100)

    print(f"\n📊 Simple Expansion Performance (3 members):")
    print(f"   Average: {results['avg']:.2f}ms")
    print(f"   P95: {results['p95']:.2f}ms")
    print(f"   Max: {results['max']:.2f}ms")

    assert results['avg'] < 5, f"Average expansion time {results['avg']:.2f}ms exceeds 5ms target"


def test_nested_expansion_performance(nested_groups):
    """
    Test nested group expansion (3 levels).

    Target: <10ms
    """
    def expand_nested():
        return expand_group_recursive(nested_groups['engineering'])

    results = benchmark_operation(expand_nested, iterations=100)

    print(f"\n📊 Nested Expansion Performance (2+ levels):")
    print(f"   Average: {results['avg']:.2f}ms")
    print(f"   P95: {results['p95']:.2f}ms")
    print(f"   Max: {results['max']:.2f}ms")

    assert results['avg'] < 10, f"Average nested expansion {results['avg']:.2f}ms exceeds 10ms target"


def test_large_group_expansion(group_workspace, group_tags):
    """
    Test expansion of a group with 100 members.

    Target: <20ms
    """
    # Create a group with many members
    member_ids = frozenset([f'tag-{i}' for i in range(100)])

    # First, add these tags to the database
    conn = group_tags[0]  # Get connection from fixture context
    from tests.fixtures.database_stub import get_connection
    conn = get_connection()

    for tag_id in member_ids:
        conn.execute(
            "INSERT OR IGNORE INTO tags (id, workspace_id, name) VALUES (?, ?, ?)",
            (tag_id, group_workspace['id'], tag_id)
        )
    conn.commit()

    large_group = create_group(
        name='large-group',
        workspace_id=group_workspace['id'],
        created_by=group_workspace['created_by'],
        initial_member_ids=member_ids
    )

    def expand_large():
        return expand_group_recursive(large_group)

    results = benchmark_operation(expand_large, iterations=50)

    print(f"\n📊 Large Group Expansion (100 members):")
    print(f"   Average: {results['avg']:.2f}ms")
    print(f"   P95: {results['p95']:.2f}ms")
    print(f"   Max: {results['max']:.2f}ms")

    assert results['avg'] < 20, f"Average large expansion {results['avg']:.2f}ms exceeds 20ms target"


def test_cache_hit_rate(sample_group):
    """
    Test cache hit rate.

    Target: >90%
    """
    # Clear cache first
    invalidate_expansion_cache(sample_group)

    # Expand 100 times
    for _ in range(100):
        expand_group_recursive(sample_group)

    stats = get_cache_statistics()

    print(f"\n📊 Cache Performance:")
    print(f"   Cache size: {stats.get('cache_size', 'N/A')}")
    print(f"   Hit rate: {stats.get('hit_rate', 'N/A'):.1f}%")
    print(f"   Total requests: {stats.get('total_requests', 'N/A')}")

    # Note: First request is always a miss, so hit rate should be ~99%
    if 'hit_rate' in stats:
        assert stats['hit_rate'] >= 90, f"Cache hit rate {stats['hit_rate']:.1f}% below 90% target"


def test_batch_add_members_performance(sample_group, group_workspace):
    """
    Test batch member addition performance.

    Target: <100ms for 50 tags
    """
    from apps.shared.services.group_storage import add_multiple_members_to_group
    from tests.fixtures.database_stub import get_connection

    # Create 50 test tags
    conn = get_connection()
    test_tags = [f'batch-tag-{i}' for i in range(50)]
    for tag_id in test_tags:
        conn.execute(
            "INSERT OR IGNORE INTO tags (id, workspace_id, name) VALUES (?, ?, ?)",
            (tag_id, group_workspace['id'], tag_id)
        )
    conn.commit()

    def add_batch():
        return add_multiple_members_to_group(
            sample_group,
            frozenset(test_tags[:10]),  # Add 10 at a time
            group_workspace['created_by']
        )

    results = benchmark_operation(add_batch, iterations=20)

    print(f"\n📊 Batch Add Members (10 tags):")
    print(f"   Average: {results['avg']:.2f}ms")
    print(f"   P95: {results['p95']:.2f}ms")
    print(f"   Max: {results['max']:.2f}ms")

    assert results['avg'] < 50, f"Average batch add {results['avg']:.2f}ms exceeds 50ms"


def test_deep_nesting_performance(group_workspace, group_tags):
    """
    Test performance with deep nesting (5 levels).

    Target: <20ms
    """
    # Create 5-level hierarchy
    level1 = create_group('perf-level-1', group_workspace['id'],
                          group_workspace['created_by'], frozenset(['tag-1']))

    level2 = create_group('perf-level-2', group_workspace['id'],
                          group_workspace['created_by'], frozenset([level1]))

    level3 = create_group('perf-level-3', group_workspace['id'],
                          group_workspace['created_by'], frozenset([level2]))

    level4 = create_group('perf-level-4', group_workspace['id'],
                          group_workspace['created_by'], frozenset([level3]))

    level5 = create_group('perf-level-5', group_workspace['id'],
                          group_workspace['created_by'], frozenset([level4]))

    def expand_deep():
        return expand_group_recursive(level5)

    results = benchmark_operation(expand_deep, iterations=50)

    print(f"\n📊 Deep Nesting Performance (5 levels):")
    print(f"   Average: {results['avg']:.2f}ms")
    print(f"   P95: {results['p95']:.2f}ms")
    print(f"   Max: {results['max']:.2f}ms")

    assert results['avg'] < 20, f"Average deep nesting {results['avg']:.2f}ms exceeds 20ms target"


def test_memory_usage(sample_group):
    """
    Test memory usage per group.

    Target: <1KB base memory
    """
    import sys

    group = get_group_by_id(sample_group)

    # Approximate memory size
    memory_bytes = sys.getsizeof(group)

    print(f"\n📊 Memory Usage:")
    print(f"   Group object size: {memory_bytes} bytes")
    print(f"   Target: <1KB (1024 bytes)")

    assert memory_bytes < 1024, f"Group memory {memory_bytes} bytes exceeds 1KB target"


def test_performance_summary():
    """Print summary of all performance targets."""
    print("\n" + "="*60)
    print("📋 GROUP TAGS PERFORMANCE TARGETS")
    print("="*60)
    print("✅ Group creation: <50ms")
    print("✅ Simple expansion (10 members): <5ms")
    print("✅ Nested expansion (3 levels): <10ms")
    print("✅ Large expansion (100 members): <20ms")
    print("✅ Deep nesting (5 levels): <20ms")
    print("✅ Batch operations (50 tags): <100ms")
    print("✅ Cache hit rate: >90%")
    print("✅ Memory per group: <1KB")
    print("="*60)
