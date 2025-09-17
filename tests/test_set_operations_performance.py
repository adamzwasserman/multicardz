"""
Performance Tests for Polymorphic Set Operations.

Validates that set operations meet performance targets:
- 1,000 cards: <10ms
- 5,000 cards: <25ms
- 10,000 cards: <50ms

Also tests cache effectiveness and optimization strategies.
"""

import random
import time
from datetime import datetime, timedelta

import pytest

from apps.shared.models.card import CardSummary
from apps.shared.models.user_preferences import UserPreferences, ViewSettings
from apps.shared.services.set_operations_unified import (
    apply_unified_operations,
    clear_unified_cache,
    get_unified_metrics,
    validate_performance_targets,
)


class TestSetOperationsPerformance:
    """Performance benchmarks for set operations."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear cache before each test."""
        clear_unified_cache()

    def generate_test_cards(self, count: int) -> frozenset[CardSummary]:
        """Generate test cards with realistic tag distributions."""
        tags_pool = [
            "urgent",
            "bug",
            "feature",
            "backend",
            "frontend",
            "api",
            "database",
            "ui",
            "high",
            "medium",
            "low",
            "assigned",
            "review",
            "testing",
            "documentation",
            "performance",
            "security",
            "refactor",
            "enhancement",
            "critical",
        ]

        cards = []
        for i in range(count):
            # Realistic tag distribution: 1-5 tags per card
            num_tags = random.randint(1, 5)
            card_tags = frozenset(random.sample(tags_pool, num_tags))

            card = CardSummary(
                id=f"CARD{i+1:04d}",
                title=f"Test Card {i+1}",
                tags=card_tags,
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 365)),
                modified_at=datetime.utcnow() - timedelta(hours=random.randint(0, 24)),
            )
            cards.append(card)

        return frozenset(cards)

    def generate_tag_counts(self, cards: frozenset[CardSummary]) -> list[tuple]:
        """Generate tag counts for optimization."""
        tag_counts = {}
        for card in cards:
            for tag in card.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return [(tag, count) for tag, count in tag_counts.items()]

    @pytest.mark.performance
    def test_1000_cards_performance(self):
        """Test performance with 1,000 cards - target <10ms."""
        cards = self.generate_test_cards(1000)
        tag_counts = self.generate_tag_counts(cards)

        # Create realistic operation sequence
        operations = [
            ("intersection", [("urgent", 45), ("bug", 123)]),
            ("difference", [("resolved", 12)]),
        ]

        start_time = time.perf_counter()
        result = apply_unified_operations(cards, operations)
        end_time = time.perf_counter()

        execution_time_ms = (end_time - start_time) * 1000

        # Validate performance target
        assert (
            execution_time_ms < 10.0
        ), f"Execution took {execution_time_ms:.2f}ms, expected <10ms"
        assert validate_performance_targets(2, 1000, execution_time_ms)

        # Validate result structure
        assert isinstance(result.cards, frozenset)
        assert result.operations_applied <= 2
        assert not result.cache_hit  # First run

    @pytest.mark.performance
    def test_5000_cards_performance(self):
        """Test performance with 5,000 cards - target <25ms."""
        cards = self.generate_test_cards(5000)

        operations = [
            ("intersection", [("priority", 234), ("urgent", 567)]),
            ("union", [("high", 345), ("medium", 678)]),
            ("difference", [("resolved", 45), ("completed", 23)]),
        ]

        start_time = time.perf_counter()
        result = apply_unified_operations(cards, operations)
        end_time = time.perf_counter()

        execution_time_ms = (end_time - start_time) * 1000

        assert (
            execution_time_ms < 25.0
        ), f"Execution took {execution_time_ms:.2f}ms, expected <25ms"
        assert validate_performance_targets(3, 5000, execution_time_ms)

    @pytest.mark.performance
    def test_10000_cards_performance(self):
        """Test performance with 10,000 cards - target <50ms."""
        cards = self.generate_test_cards(10000)

        operations = [
            ("intersection", [("critical", 123), ("security", 234)]),
            ("union", [("enhancement", 456), ("refactor", 345)]),
            ("difference", [("testing", 567), ("documentation", 123)]),
        ]

        start_time = time.perf_counter()
        result = apply_unified_operations(cards, operations)
        end_time = time.perf_counter()

        execution_time_ms = (end_time - start_time) * 1000

        assert (
            execution_time_ms < 50.0
        ), f"Execution took {execution_time_ms:.2f}ms, expected <50ms"
        assert validate_performance_targets(3, 10000, execution_time_ms)

    @pytest.mark.performance
    def test_cache_effectiveness(self):
        """Test that caching improves performance for repeated operations."""
        from apps.shared.services.set_operations_unified import ThreadSafeCache

        # Generate cards ONCE to ensure same input for both executions
        cards = self.generate_test_cards(1000)

        operations = [
            ("intersection", [("urgent", 45), ("bug", 67)]),
            ("union", [("high", 89), ("medium", 123)]),
        ]

        # Create explicit cache instance to ensure consistency
        cache = ThreadSafeCache()

        # First execution (cache miss)
        start_time = time.perf_counter()
        result1 = apply_unified_operations(
            cards, operations, use_cache=True, cache=cache
        )
        first_time = (time.perf_counter() - start_time) * 1000

        # Second execution with SAME cards and operations (cache hit)
        start_time = time.perf_counter()
        result2 = apply_unified_operations(
            cards, operations, use_cache=True, cache=cache
        )
        second_time = (time.perf_counter() - start_time) * 1000

        # Validate cache effectiveness
        assert not result1.cache_hit
        assert result2.cache_hit
        assert result1.cards == result2.cards
        assert second_time < first_time  # Cache should be faster

        # Check cache metrics - pass the same cache instance used in the test
        metrics = get_unified_metrics(cache)
        assert metrics.cache_hit_rate > 0.0

    @pytest.mark.performance
    def test_short_circuit_optimization(self):
        """Test that operations short-circuit on empty results."""
        cards = self.generate_test_cards(1000)

        operations = [
            ("intersection", [("urgent", 45), ("bug", 67)]),
            (
                "intersection",
                [("nonexistent_tag", 0)],
            ),  # This should result in empty set
            ("union", [("should_not_execute", 100)]),  # This should not execute
        ]

        start_time = time.perf_counter()
        result = apply_unified_operations(cards, operations)
        execution_time_ms = (time.perf_counter() - start_time) * 1000

        # Should short-circuit and be very fast
        assert (
            execution_time_ms < 5.0
        ), f"Short-circuit took {execution_time_ms:.2f}ms, expected <5ms"
        assert result.short_circuited
        assert result.operations_applied < len(operations)
        assert len(result.cards) == 0

    @pytest.mark.performance
    def test_tag_selectivity_optimization(self):
        """Test that tags are processed in order of selectivity."""
        # Create cards with predictable tag distributions
        cards = []
        for i in range(1000):
            tags = set()
            if i < 900:  # 90% have "common"
                tags.add("common")
            if i < 100:  # 10% have "rare"
                tags.add("rare")
            if i < 10:  # 1% have "unique"
                tags.add("unique")

            card = CardSummary(
                id=f"CARD{i+1:04d}", title=f"Test Card {i+1}", tags=frozenset(tags)
            )
            cards.append(card)

        cards_set = frozenset(cards)

        # Operation with tags in non-optimal order
        operations = [
            ("intersection", [("common", 900), ("rare", 100), ("unique", 10)])
        ]

        start_time = time.perf_counter()
        result = apply_unified_operations(cards_set, operations, optimize_order=True)
        execution_time_ms = (time.perf_counter() - start_time) * 1000

        # Should be fast due to optimization
        assert execution_time_ms < 10.0
        # Should find cards that have all three tags (most selective wins)
        assert len(result.cards) == 10  # Only 10 cards have "unique"

    @pytest.mark.performance
    def test_user_preference_overhead(self):
        """Test that user preference application adds minimal overhead."""
        cards = self.generate_test_cards(1000)
        user_prefs = UserPreferences(
            user_id="test_user", view_settings=ViewSettings(cards_start_visible=True)
        )

        operations = [("intersection", [("urgent", 45), ("bug", 67)])]

        # Without user preferences
        start_time = time.perf_counter()
        result1 = apply_unified_operations(cards, operations, user_preferences=None)
        time_without_prefs = (time.perf_counter() - start_time) * 1000

        # With user preferences
        start_time = time.perf_counter()
        result2 = apply_unified_operations(
            cards, operations, user_preferences=user_prefs
        )
        time_with_prefs = (time.perf_counter() - start_time) * 1000

        # Overhead should be minimal
        overhead = time_with_prefs - time_without_prefs
        assert (
            overhead < 1.0
        ), f"User preference overhead {overhead:.2f}ms, expected <1ms"

    @pytest.mark.performance
    def test_memory_efficiency(self):
        """Test memory usage remains stable with large datasets."""
        import tracemalloc

        tracemalloc.start()

        # Baseline measurement
        current, peak = tracemalloc.get_traced_memory()
        baseline_memory = current

        # Process large dataset
        cards = self.generate_test_cards(5000)
        operations = [
            ("intersection", [("urgent", 234), ("high", 345)]),
            ("union", [("medium", 456), ("low", 567)]),
        ]

        result = apply_unified_operations(cards, operations)

        # Memory measurement after operation
        current, peak = tracemalloc.get_traced_memory()
        memory_used = current - baseline_memory

        tracemalloc.stop()

        # Memory should be proportional to result size, not input size
        memory_mb = memory_used / (1024 * 1024)

        # Allow reasonable memory usage (should be much less than storing full dataset)
        assert memory_mb < 10.0, f"Memory usage {memory_mb:.2f}MB too high"

        # Validate immutability (original cards unchanged)
        assert len(cards) == 5000  # Original set unchanged

    @pytest.mark.performance
    def test_polymorphic_operation_types(self):
        """Test performance across different operation types."""
        cards = self.generate_test_cards(1000)

        test_cases = [
            ("intersection", [("urgent", 45), ("bug", 67)]),
            ("union", [("high", 89), ("medium", 123)]),
            ("difference", [("resolved", 12), ("completed", 8)]),
        ]

        for operation_type, tags_with_counts in test_cases:
            operations = [(operation_type, tags_with_counts)]

            start_time = time.perf_counter()
            result = apply_unified_operations(cards, operations)
            execution_time_ms = (time.perf_counter() - start_time) * 1000

            # All operation types should meet performance targets
            assert (
                execution_time_ms < 10.0
            ), f"{operation_type} took {execution_time_ms:.2f}ms"
            assert isinstance(result.cards, frozenset)
            assert result.operations_applied == 1


class TestSetOperationsStress:
    """Stress tests for extreme conditions."""

    @pytest.mark.stress
    def test_very_large_dataset_20k(self):
        """Stress test with very large dataset (20,000 cards)."""
        cards = []
        tags_pool = [f"tag_{i}" for i in range(50)]  # 50 different tags

        for i in range(20000):
            num_tags = random.randint(2, 8)
            card_tags = frozenset(random.sample(tags_pool, num_tags))

            card = CardSummary(
                id=f"STRESS{i+1:05d}", title=f"Stress Test Card {i+1}", tags=card_tags
            )
            cards.append(card)

        cards_set = frozenset(cards)

        operations = [
            ("intersection", [("tag_1", 400), ("tag_2", 400)]),
            ("union", [("tag_3", 400), ("tag_4", 400)]),
            ("difference", [("tag_5", 200)]),
        ]

        start_time = time.perf_counter()
        result = apply_unified_operations(cards_set, operations)
        execution_time_ms = (time.perf_counter() - start_time) * 1000

        # Should scale linearly - allow more time for large dataset
        expected_max_time = 100.0  # 100ms for 20k cards
        assert (
            execution_time_ms < expected_max_time
        ), f"Stress test took {execution_time_ms:.2f}ms"

    @pytest.mark.stress
    def test_mega_dataset_100k(self):
        """Mega stress test with 100,000 cards."""
        import gc

        gc.collect()  # Clean up before test

        cards = []
        tags_pool = [f"tag_{i}" for i in range(100)]  # 100 different tags

        # Generate cards in batches to manage memory
        batch_size = 5000
        for batch in range(0, 100000, batch_size):
            batch_cards = []
            for i in range(batch, min(batch + batch_size, 100000)):
                num_tags = random.randint(1, 6)
                card_tags = frozenset(random.sample(tags_pool, num_tags))

                card = CardSummary(
                    id=f"MEGA{i+1:06d}", title=f"Mega Card {i+1}", tags=card_tags
                )
                batch_cards.append(card)
            cards.extend(batch_cards)

        cards_set = frozenset(cards)

        # Use highly selective operations for performance
        operations = [
            (
                "intersection",
                [("tag_1", 1000), ("tag_2", 1000)],
            ),  # Should be highly selective
            ("difference", [("tag_99", 500)]),  # Remove some results
        ]

        start_time = time.perf_counter()
        result = apply_unified_operations(cards_set, operations)
        execution_time_ms = (time.perf_counter() - start_time) * 1000

        # Target: 500ms for 100k cards (5ms per 1k cards)
        expected_max_time = 500.0
        assert (
            execution_time_ms < expected_max_time
        ), f"100k cards took {execution_time_ms:.2f}ms, expected <{expected_max_time}ms"

        # Validate memory efficiency
        assert len(result.cards) < len(cards_set), "Should filter down the dataset"

    @pytest.mark.stress
    def test_ultra_dataset_1M(self):
        """Ultra stress test with 1,000,000 cards."""
        import gc
        import tracemalloc

        gc.collect()
        tracemalloc.start()

        # Use efficient generation to avoid memory explosion
        def generate_card_batch(start_idx, batch_size, tags_pool):
            """Generate a batch of cards efficiently."""
            batch = []
            for i in range(start_idx, start_idx + batch_size):
                num_tags = random.randint(1, 4)  # Fewer tags for efficiency
                card_tags = frozenset(random.sample(tags_pool, num_tags))

                card = CardSummary(
                    id=f"ULTRA{i+1:07d}", title=f"Ultra Card {i+1}", tags=card_tags
                )
                batch.append(card)
            return batch

        # Generate 1M cards in chunks
        tags_pool = [f"tag_{i}" for i in range(200)]  # 200 different tags
        all_cards = []
        batch_size = 10000  # 10k cards per batch

        print(f"Generating 1M cards in {1000000 // batch_size} batches...")

        for batch_start in range(0, 1000000, batch_size):
            if batch_start % 100000 == 0:  # Progress indicator
                print(f"Generated {batch_start:,} cards...")

            batch = generate_card_batch(batch_start, batch_size, tags_pool)
            all_cards.extend(batch)

            # Force garbage collection every 10 batches
            if (batch_start // batch_size) % 10 == 0:
                gc.collect()

        cards_set = frozenset(all_cards)
        print(f"Generated {len(cards_set):,} total cards")

        # Use extremely selective operations for 1M scale
        operations = [
            ("intersection", [("tag_1", 5000), ("tag_2", 5000)]),  # Very selective
        ]

        print("Starting 1M card operation with TURBO mode...")
        start_time = time.perf_counter()
        result = apply_unified_operations(
            cards_set,
            operations,
            use_turbo=True,
            use_parallel=True,
            use_cache=False,  # Disable cache for pure performance test
        )
        execution_time_ms = (time.perf_counter() - start_time) * 1000

        # Target: 1000ms (1 second) for 1M cards
        expected_max_time = 1000.0
        print(f"1M cards operation completed in {execution_time_ms:.2f}ms")

        # Memory check
        current, peak = tracemalloc.get_traced_memory()
        memory_mb = peak / (1024 * 1024)
        print(f"Peak memory usage: {memory_mb:.1f}MB")

        tracemalloc.stop()

        assert (
            execution_time_ms < expected_max_time
        ), f"1M cards took {execution_time_ms:.2f}ms, expected <{expected_max_time}ms"
        assert (
            memory_mb < 1000
        ), f"Memory usage {memory_mb:.1f}MB too high for 1M cards"  # <1GB
        assert len(result.cards) < len(cards_set), "Should filter the massive dataset"

        # Validate performance targets at scale
        assert validate_performance_targets(1, 1000000, execution_time_ms)

    @pytest.mark.stress
    def test_scaling_benchmarks(self):
        """Benchmark scaling from 1k to 100k cards."""
        scaling_results = {}
        tags_pool = [f"tag_{i}" for i in range(50)]

        test_sizes = [1000, 5000, 10000, 25000, 50000, 100000]
        operations = [("intersection", [("tag_1", 100), ("tag_2", 150)])]

        for size in test_sizes:
            print(f"Benchmarking {size:,} cards...")

            # Generate cards for this size
            cards = []
            for i in range(size):
                num_tags = random.randint(1, 4)
                card_tags = frozenset(random.sample(tags_pool, num_tags))

                card = CardSummary(
                    id=f"SCALE{i+1:06d}", title=f"Scale Card {i+1}", tags=card_tags
                )
                cards.append(card)

            cards_set = frozenset(cards)

            # Time the operation
            start_time = time.perf_counter()
            result = apply_unified_operations(cards_set, operations)
            execution_time_ms = (time.perf_counter() - start_time) * 1000

            scaling_results[size] = execution_time_ms
            print(f"{size:,} cards: {execution_time_ms:.2f}ms")

            # Check if scaling is reasonable (should be roughly linear)
            if size > 1000:
                scaling_factor = execution_time_ms / scaling_results[1000]
                size_factor = size / 1000
                efficiency = scaling_factor / size_factor

                # Should scale within 2x of linear (accounting for overhead)
                assert (
                    efficiency < 2.0
                ), f"Scaling efficiency {efficiency:.2f} too poor at {size:,} cards"

        # Print scaling summary
        print("\nScaling Results:")
        for size, time_ms in scaling_results.items():
            rate = size / time_ms if time_ms > 0 else 0
            print(f"{size:,} cards: {time_ms:.2f}ms ({rate:,.0f} cards/ms)")

    @pytest.mark.stress
    def test_memory_efficiency_large_scale(self):
        """Test memory efficiency with large datasets."""
        import gc
        import tracemalloc

        gc.collect()
        tracemalloc.start()

        # Test with 50k cards
        cards = []
        tags_pool = [f"tag_{i}" for i in range(30)]

        for i in range(50000):
            num_tags = random.randint(1, 3)
            card_tags = frozenset(random.sample(tags_pool, num_tags))

            card = CardSummary(
                id=f"MEM{i+1:05d}", title=f"Memory Test {i+1}", tags=card_tags
            )
            cards.append(card)

        cards_set = frozenset(cards)

        # Baseline memory
        current, peak = tracemalloc.get_traced_memory()
        baseline_memory = current

        # Perform multiple operations to test memory stability
        operations_list = [
            [("intersection", [("tag_1", 1000), ("tag_2", 1500)])],
            [("union", [("tag_3", 2000), ("tag_4", 1800)])],
            [("difference", [("tag_5", 500)])],
            [("intersection", [("tag_6", 1200)]), ("union", [("tag_7", 900)])],
        ]

        memory_measurements = []

        for i, operations in enumerate(operations_list):
            result = apply_unified_operations(cards_set, operations)

            current, peak = tracemalloc.get_traced_memory()
            memory_used = current - baseline_memory
            memory_measurements.append(memory_used)

            print(
                f"Operation {i+1}: {len(result.cards)} results, {memory_used/(1024*1024):.1f}MB"
            )

        tracemalloc.stop()

        # Memory should not grow significantly between operations (garbage collection working)
        max_memory = max(memory_measurements)
        min_memory = min(memory_measurements)
        memory_variance = (max_memory - min_memory) / max_memory

        assert (
            memory_variance < 0.5
        ), f"Memory variance {memory_variance:.2f} too high - possible memory leak"

    @pytest.mark.stress
    def test_concurrent_operations_simulation(self):
        """Simulate concurrent operations on large dataset."""
        import queue
        import threading

        # Generate shared dataset
        cards = []
        tags_pool = [f"tag_{i}" for i in range(40)]

        for i in range(25000):  # 25k cards for concurrent test
            num_tags = random.randint(1, 4)
            card_tags = frozenset(random.sample(tags_pool, num_tags))

            card = CardSummary(
                id=f"CONC{i+1:05d}", title=f"Concurrent Card {i+1}", tags=card_tags
            )
            cards.append(card)

        cards_set = frozenset(cards)

        # Define different operation patterns
        operation_patterns = [
            [("intersection", [("tag_1", 500), ("tag_2", 600)])],
            [("union", [("tag_3", 700), ("tag_4", 800)])],
            [("difference", [("tag_5", 200)])],
            [("intersection", [("tag_6", 400)]), ("union", [("tag_7", 300)])],
        ]

        results_queue = queue.Queue()

        def worker(pattern_id, operations):
            """Worker function for concurrent execution."""
            start_time = time.perf_counter()
            result = apply_unified_operations(cards_set, operations)
            execution_time = (time.perf_counter() - start_time) * 1000

            results_queue.put(
                {
                    "pattern_id": pattern_id,
                    "execution_time_ms": execution_time,
                    "result_count": len(result.cards),
                    "cache_hit": result.cache_hit,
                }
            )

        # Start concurrent operations
        threads = []
        for i, pattern in enumerate(operation_patterns):
            thread = threading.Thread(target=worker, args=(i, pattern))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Collect results
        concurrent_results = []
        while not results_queue.empty():
            concurrent_results.append(results_queue.get())

        # Validate concurrent performance
        for result in concurrent_results:
            execution_time = result["execution_time_ms"]
            assert (
                execution_time < 200.0
            ), f"Concurrent operation took {execution_time:.2f}ms, expected <200ms"

        print(f"Concurrent operations completed: {len(concurrent_results)} threads")
        for result in concurrent_results:
            print(
                f"Pattern {result['pattern_id']}: {result['execution_time_ms']:.2f}ms, {result['result_count']} results, cache_hit={result['cache_hit']}"
            )

        # Verify thread safety (all operations completed successfully)
        assert len(concurrent_results) == len(operation_patterns)

    @pytest.mark.stress
    def test_turbo_mode_benchmark(self):
        """Benchmark turbo mode vs regular processing."""
        try:
            from apps.shared.services.set_operations_turbo import (
                benchmark_turbo_performance,
            )
        except ImportError:
            pytest.skip("Turbo mode not available")

        # Test with 200k cards to trigger turbo mode
        benchmark_results = benchmark_turbo_performance(200000)

        print("\nTurbo Mode Benchmark Results:")
        print(f"Cards: {benchmark_results['card_count']:,}")
        print(f"Regular: {benchmark_results['regular_time_ms']:.2f}ms")
        print(f"Turbo: {benchmark_results['turbo_time_ms']:.2f}ms")
        print(f"Speedup: {benchmark_results['speedup_factor']:.2f}x")

        # Turbo should be faster for large datasets
        assert benchmark_results["turbo_time_ms"] < benchmark_results["regular_time_ms"]
        assert benchmark_results["speedup_factor"] > 1.0

        # Results should be identical
        assert (
            benchmark_results["regular_results"] == benchmark_results["turbo_results"]
        )

    @pytest.mark.stress
    def test_many_operations_sequence(self):
        """Test performance with many sequential operations."""
        cards = self.generate_test_cards(1000)

        # Create 10 sequential operations
        operations = []
        for i in range(10):
            if i % 3 == 0:
                op_type = "intersection"
            elif i % 3 == 1:
                op_type = "union"
            else:
                op_type = "difference"

            operations.append((op_type, [(f"tag_{i}", random.randint(10, 100))]))

        start_time = time.perf_counter()
        result = apply_unified_operations(frozenset(cards), operations)
        execution_time_ms = (time.perf_counter() - start_time) * 1000

        # Should handle many operations efficiently
        assert (
            execution_time_ms < 50.0
        ), f"Many operations took {execution_time_ms:.2f}ms"

    def generate_test_cards(self, count: int) -> list[CardSummary]:
        """Helper to generate test cards."""
        tags_pool = [
            "urgent",
            "bug",
            "feature",
            "backend",
            "frontend",
            "api",
            "database",
            "ui",
            "high",
            "medium",
            "low",
            "assigned",
        ]

        cards = []
        for i in range(count):
            num_tags = random.randint(1, 4)
            card_tags = frozenset(random.sample(tags_pool, num_tags))

            card = CardSummary(
                id=f"CARD{i+1:04d}", title=f"Test Card {i+1}", tags=card_tags
            )
            cards.append(card)

        return cards
