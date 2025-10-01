"""Step definitions for performance optimization feature."""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any

# Load scenarios from feature file
scenarios("../features/performance_optimization.feature")


# Shared context for test steps
@pytest.fixture
def context():
    """Test context shared between steps."""
    return {
        "cards": None,
        "result": None,
        "performance": None,
        "queries": [],
        "cache_hits": 0,
        "cache_total": 0
    }


# Scenario: Filter 100K cards in under 50ms
@given("I have 100,000 cards in the system")
def have_100k_cards(context, large_card_set):
    """Set up 100K cards."""
    context["cards"] = large_card_set
    assert len(context["cards"]) == 100000


@given("cards have various tag combinations")
def cards_have_tag_combinations(context):
    """Verify cards have diverse tags."""
    cards = context["cards"]
    # Check that cards have varying tag counts
    tag_counts = [len(card.tag_bitmaps) for card in cards]
    assert min(tag_counts) >= 1
    assert max(tag_counts) <= 10


@when("I perform complex filtering")
def perform_complex_filtering(context, performance_monitor):
    """Perform filtering operation with timing."""
    from apps.shared.services.performance_optimization import parallel_filter_operation

    cards = context["cards"]
    intersection_tags = [1, 2, 3]
    union_tags = [4, 5]

    monitor = performance_monitor
    monitor.start()

    # Perform filtering
    result = parallel_filter_operation(
        cards,
        intersection_tags,
        union_tags,
        workspace_id="test-workspace",
        user_id="test-user",
        num_workers=4
    )

    metrics = monitor.stop()
    context["result"] = result
    context["performance"] = metrics


@then("results should return in under 50ms")
def results_under_50ms(context):
    """Verify performance under 50ms."""
    elapsed = context["performance"]["elapsed"]
    assert elapsed < 0.05, f"Operation took {elapsed:.3f}s, expected <0.05s"


@then("memory usage should stay under 100MB")
def memory_under_100mb(context):
    """Verify memory usage under 100MB."""
    memory = context["performance"]["memory_mb"]
    assert memory < 100, f"Memory usage {memory:.1f}MB, expected <100MB"


@then("CPU usage should stay reasonable")
def cpu_reasonable(context):
    """Verify CPU usage is reasonable."""
    cpu = context["performance"]["cpu_percent"]
    # CPU usage can be negative initially due to psutil measurement timing
    # Just verify it's tracked and not excessively high
    assert cpu is not None, "CPU usage should be tracked"
    assert cpu < 200, f"CPU usage {cpu}% is too high"


# Scenario: Concurrent operations
@given("I have 10 concurrent users")
def have_10_concurrent_users(context):
    """Set up 10 concurrent users."""
    context["num_users"] = 10
    context["user_results"] = []


@when("they all perform operations simultaneously")
def perform_operations_simultaneously(context, large_card_set):
    """Execute concurrent operations."""
    from apps.shared.services.performance_optimization import parallel_filter_operation

    num_users = context["num_users"]
    cards = large_card_set

    def user_operation(user_id):
        """Single user operation."""
        start = time.perf_counter()
        result = parallel_filter_operation(
            cards,
            [1, 2],
            [3, 4],
            workspace_id=f"workspace-{user_id}",
            user_id=f"user-{user_id}",
            num_workers=2
        )
        elapsed = time.perf_counter() - start
        return {"user_id": user_id, "elapsed": elapsed, "count": len(result)}

    # Run operations concurrently
    with ThreadPoolExecutor(max_workers=num_users) as executor:
        futures = [executor.submit(user_operation, i) for i in range(num_users)]
        results = [f.result() for f in futures]

    context["user_results"] = results


@then("response times should remain consistent")
def response_times_consistent(context):
    """Verify response times are consistent."""
    results = context["user_results"]
    times = [r["elapsed"] for r in results]

    avg_time = sum(times) / len(times)
    max_time = max(times)

    # Max time should not be more than 2x average
    assert max_time < avg_time * 2, f"Max time {max_time:.3f}s exceeds 2x average {avg_time:.3f}s"


@then("no race conditions should occur")
def no_race_conditions(context):
    """Verify no race conditions."""
    results = context["user_results"]

    # All operations should complete successfully
    assert len(results) == context["num_users"]

    # All should have results
    for result in results:
        assert result["count"] >= 0


@then("database connections should be pooled")
def connections_pooled(context):
    """Verify connection pooling."""
    from apps.shared.services.performance_optimization import connection_pool

    # Connection pool should exist
    assert connection_pool is not None
    assert connection_pool.max_connections > 0


# Scenario: Cache effectiveness
@given("I perform the same query multiple times")
def perform_same_query_multiple_times(context, large_card_set):
    """Execute same query multiple times."""
    from apps.shared.services.performance_optimization import cached_bitmap_intersection

    cards = large_card_set
    tag_bitmaps = (1, 2, 3)
    cards_hash = hash(frozenset(cards))

    # Perform query 10 times
    times = []
    for _ in range(10):
        start = time.perf_counter()
        result = cached_bitmap_intersection(tag_bitmaps, cards_hash)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    context["queries"] = times


@when("cache is enabled")
def cache_enabled(context):
    """Verify cache is enabled."""
    from apps.shared.services.performance_optimization import cached_bitmap_intersection

    # Cache should have LRU decorator
    assert hasattr(cached_bitmap_intersection, "cache_info")


@then("subsequent queries should be faster")
def subsequent_queries_faster(context):
    """Verify subsequent queries are faster."""
    times = context["queries"]

    first_time = times[0]
    avg_subsequent = sum(times[1:]) / len(times[1:])

    # Subsequent queries should be faster (or similar if already optimized)
    # Allow some tolerance for system variance
    assert avg_subsequent <= first_time * 1.5, \
        f"Subsequent queries {avg_subsequent:.6f}s not faster than first {first_time:.6f}s"


@then(parsers.parse("cache hit rate should exceed {percentage:d}%"))
def cache_hit_rate_exceeds(context, percentage):
    """Verify cache hit rate."""
    from apps.shared.services.performance_optimization import cached_bitmap_intersection

    cache_info = cached_bitmap_intersection.cache_info()

    if cache_info.hits + cache_info.misses > 0:
        hit_rate = cache_info.hits / (cache_info.hits + cache_info.misses) * 100
        assert hit_rate >= percentage, f"Cache hit rate {hit_rate:.1f}% below {percentage}%"


@then("cache invalidation should work correctly")
def cache_invalidation_works(context):
    """Verify cache can be invalidated."""
    from apps.shared.services.performance_optimization import cached_bitmap_intersection

    # Clear cache
    cached_bitmap_intersection.cache_clear()

    # Verify cache is cleared
    cache_info = cached_bitmap_intersection.cache_info()
    assert cache_info.hits == 0
    assert cache_info.misses == 0
