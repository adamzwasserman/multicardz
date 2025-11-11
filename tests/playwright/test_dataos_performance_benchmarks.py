"""
DATAOS Performance Benchmark Tests

Measures DOM extraction performance without caching to ensure:
1. 60 FPS requirement (<16ms for any operation)
2. Scalability with 100, 500, 1000, 5000 tags
3. No performance degradation from cache removal
4. Baseline metrics for regression detection

Test Scenarios:
- Small workload: 100 tags (should be <1ms)
- Medium workload: 500 tags (should be <5ms)
- Large workload: 1000 tags (should be <10ms)
- XL workload: 5000 tags (should be <16ms for 60 FPS)
"""

import pytest
import time
import statistics
from playwright.sync_api import Page, expect


@pytest.fixture
def setup_performance_test_page(page: Page):
    """
    Set up test page with configurable number of tags for performance testing.
    """
    page.goto("http://localhost:8011/")
    page.wait_for_selector('[data-zone-type]')
    page.wait_for_function("window.dragDropSystem !== undefined")
    return page


class TestDOMExtractionPerformance:
    """
    Performance benchmarks for deriveStateFromDOM() without caching.
    """

    @pytest.mark.parametrize("tag_count,max_duration_ms", [
        (100, 1),     # Small: should be sub-millisecond
        (500, 5),     # Medium: should be <5ms
        (1000, 10),   # Large: should be <10ms (original target)
        (5000, 16),   # XL: should be <16ms for 60 FPS
    ])
    def test_derive_state_performance(self, setup_performance_test_page: Page, tag_count: int, max_duration_ms: float):
        """
        Test deriveStateFromDOM() performance across different tag counts.
        Ensures DATAOS compliance doesn't degrade performance.
        """
        page = setup_performance_test_page

        # Setup: Create specified number of tags
        page.evaluate(f"""
            const cloud = document.querySelector('.cloud-user .tags-wrapper');
            const includeZone = document.querySelector('[data-zone-type="include"]');
            const excludeZone = document.querySelector('[data-zone-type="exclude"]');

            const includeCollection = includeZone?.querySelector('.tag-collection');
            const excludeCollection = excludeZone?.querySelector('.tag-collection');

            // Create {tag_count} tags distributed across zones
            for (let i = 0; i < {tag_count}; i++) {{
                const tag = document.createElement('span');
                tag.className = 'tag';
                tag.setAttribute('data-tag', `perf-tag-${{i}}`);
                tag.setAttribute('data-tag-id', `perf-id-${{i}}`);
                tag.setAttribute('data-type', 'user-tag');
                tag.setAttribute('draggable', 'true');
                tag.textContent = `perf-tag-${{i}}`;

                // Distribute: 70% in cloud, 15% in include, 15% in exclude
                if (i % 10 < 7) {{
                    tag.classList.add('tag-cloud');
                    cloud?.appendChild(tag);
                }} else if (i % 10 < 8.5) {{
                    tag.classList.add('tag-active');
                    includeCollection?.appendChild(tag);
                }} else {{
                    tag.classList.add('tag-active');
                    excludeCollection?.appendChild(tag);
                }}
            }}
        """)

        # Benchmark: Run deriveStateFromDOM() 10 times and measure
        result = page.evaluate("""
            const iterations = 10;
            const durations = [];

            for (let i = 0; i < iterations; i++) {
                const start = performance.now();
                const state = window.dragDropSystem.deriveStateFromDOM();
                const end = performance.now();
                durations.push(end - start);
            }

            // Calculate statistics
            const sum = durations.reduce((a, b) => a + b, 0);
            const avg = sum / iterations;
            const max = Math.max(...durations);
            const min = Math.min(...durations);

            // Calculate median
            const sorted = durations.slice().sort((a, b) => a - b);
            const median = iterations % 2 === 0
                ? (sorted[iterations / 2 - 1] + sorted[iterations / 2]) / 2
                : sorted[Math.floor(iterations / 2)];

            // Calculate standard deviation
            const variance = durations.reduce((acc, val) => acc + Math.pow(val - avg, 2), 0) / iterations;
            const stdDev = Math.sqrt(variance);

            return {
                durations: durations,
                avg: avg,
                max: max,
                min: min,
                median: median,
                stdDev: stdDev
            };
        """)

        # Assertions
        print(f"\n=== Performance Results for {tag_count} tags ===")
        print(f"Average: {result['avg']:.3f}ms")
        print(f"Median:  {result['median']:.3f}ms")
        print(f"Min:     {result['min']:.3f}ms")
        print(f"Max:     {result['max']:.3f}ms")
        print(f"StdDev:  {result['stdDev']:.3f}ms")
        print(f"Target:  <{max_duration_ms}ms")

        # Primary assertion: Maximum duration must be under target
        assert result['max'] < max_duration_ms, \
            f"Max duration {result['max']:.3f}ms exceeds {max_duration_ms}ms target for {tag_count} tags"

        # Secondary assertion: Average should be well below target (80% threshold)
        avg_threshold = max_duration_ms * 0.8
        assert result['avg'] < avg_threshold, \
            f"Average {result['avg']:.3f}ms should be <{avg_threshold}ms (80% of target) for {tag_count} tags"

        # Tertiary assertion: Standard deviation should be low (consistent performance)
        max_std_dev = max_duration_ms * 0.3  # StdDev should be <30% of target
        assert result['stdDev'] < max_std_dev, \
            f"StdDev {result['stdDev']:.3f}ms exceeds {max_std_dev}ms (30% of target) - performance is inconsistent"

    def test_no_caching_performance_impact(self, setup_performance_test_page: Page):
        """
        Test that removing caching doesn't cause performance regression.
        Compare 10 sequential calls - all should have similar performance.
        """
        page = setup_performance_test_page

        # Setup: Create 1000 tags for realistic load
        page.evaluate("""
            const cloud = document.querySelector('.cloud-user .tags-wrapper');
            for (let i = 0; i < 1000; i++) {
                const tag = document.createElement('span');
                tag.className = 'tag tag-cloud';
                tag.setAttribute('data-tag', `nocache-tag-${i}`);
                tag.setAttribute('data-tag-id', `nocache-id-${i}`);
                tag.setAttribute('draggable', 'true');
                tag.textContent = `nocache-tag-${i}`;
                cloud?.appendChild(tag);
            }
        """)

        # Test: Run 10 calls and verify consistent performance (no cache benefit)
        result = page.evaluate("""
            const calls = 10;
            const durations = [];

            for (let i = 0; i < calls; i++) {
                const start = performance.now();
                window.dragDropSystem.deriveStateFromDOM();
                const end = performance.now();
                durations.push(end - start);
            }

            const avg = durations.reduce((a, b) => a + b, 0) / calls;
            const max = Math.max(...durations);
            const min = Math.min(...durations);

            return {
                durations: durations,
                avg: avg,
                max: max,
                min: min,
                firstCallDuration: durations[0],
                lastCallDuration: durations[calls - 1],
                varianceRatio: max / min  // Should be close to 1.0 (no caching effect)
            };
        """)

        print(f"\n=== No-Cache Performance Analysis ===")
        print(f"First call: {result['firstCallDuration']:.3f}ms")
        print(f"Last call:  {result['lastCallDuration']:.3f}ms")
        print(f"Average:    {result['avg']:.3f}ms")
        print(f"Variance ratio (max/min): {result['varianceRatio']:.2f}x")

        # Assertion: Variance ratio should be close to 1.0 (indicating no caching effect)
        # Allow up to 2.5x variance for JIT compilation and GC effects
        assert result['varianceRatio'] < 2.5, \
            f"Variance ratio {result['varianceRatio']:.2f}x suggests caching may still exist"

        # Assertion: All calls should be under 10ms
        assert result['max'] < 10, \
            f"Maximum call {result['max']:.3f}ms exceeds 10ms for 1000 tags"


class TestQueryOptimization:
    """
    Test that DOM queries are optimized for performance without caching.
    """

    def test_selector_performance(self, setup_performance_test_page: Page):
        """
        Test that specific selector strategies are performant.
        """
        page = setup_performance_test_page

        # Setup: Create 2000 tags for query stress test
        page.evaluate("""
            const cloud = document.querySelector('.cloud-user .tags-wrapper');
            for (let i = 0; i < 2000; i++) {
                const tag = document.createElement('span');
                tag.className = 'tag tag-cloud';
                tag.setAttribute('data-tag', `selector-tag-${i}`);
                tag.setAttribute('data-tag-id', `selector-id-${i}`);
                tag.setAttribute('draggable', 'true');
                tag.textContent = `selector-tag-${i}`;
                cloud?.appendChild(tag);
            }
        """)

        # Test different query strategies
        result = page.evaluate("""
            const iterations = 100;
            const strategies = {};

            // Strategy 1: querySelectorAll with attribute selector
            let start = performance.now();
            for (let i = 0; i < iterations; i++) {
                document.querySelectorAll('[data-tag]');
            }
            strategies.attributeSelector = (performance.now() - start) / iterations;

            // Strategy 2: querySelectorAll with class selector
            start = performance.now();
            for (let i = 0; i < iterations; i++) {
                document.querySelectorAll('.tag-selected');
            }
            strategies.classSelector = (performance.now() - start) / iterations;

            // Strategy 3: querySelectorAll with compound selector
            start = performance.now();
            for (let i = 0; i < iterations; i++) {
                document.querySelectorAll('[data-tag].tag-selected');
            }
            strategies.compoundSelector = (performance.now() - start) / iterations;

            // Strategy 4: querySelector single element
            start = performance.now();
            for (let i = 0; i < iterations; i++) {
                document.querySelector('[data-tag="selector-tag-0"]');
            }
            strategies.singleElementQuery = (performance.now() - start) / iterations;

            return strategies;
        """)

        print(f"\n=== Selector Performance (avg over 100 iterations) ===")
        for strategy, duration in result.items():
            print(f"{strategy}: {duration:.4f}ms")

        # Assertions: All query strategies should be fast
        assert result['attributeSelector'] < 5, \
            f"Attribute selector {result['attributeSelector']:.4f}ms too slow"
        assert result['classSelector'] < 2, \
            f"Class selector {result['classSelector']:.4f}ms too slow"
        assert result['compoundSelector'] < 5, \
            f"Compound selector {result['compoundSelector']:.4f}ms too slow"
        assert result['singleElementQuery'] < 1, \
            f"Single element query {result['singleElementQuery']:.4f}ms too slow"

    def test_zone_discovery_performance(self, setup_performance_test_page: Page):
        """
        Test that discoverZones() is performant without caching.
        """
        page = setup_performance_test_page

        # Setup: Ensure multiple zones exist
        page.evaluate("""
            // Add tags to multiple zones for realistic discovery
            const zones = document.querySelectorAll('[data-zone-type]:not([data-zone-type="tag-cloud"])');
            zones.forEach((zone, zoneIndex) => {
                const collection = zone.querySelector('.tag-collection');
                if (collection) {
                    for (let i = 0; i < 50; i++) {
                        const tag = document.createElement('span');
                        tag.className = 'tag tag-active';
                        tag.setAttribute('data-tag', `zone${zoneIndex}-tag-${i}`);
                        tag.setAttribute('data-tag-id', `zone${zoneIndex}-id-${i}`);
                        tag.setAttribute('draggable', 'true');
                        tag.textContent = `zone${zoneIndex}-tag-${i}`;
                        collection.appendChild(tag);
                    }
                }
            });
        """)

        # Test discoverZones() performance
        result = page.evaluate("""
            const iterations = 100;
            const durations = [];

            for (let i = 0; i < iterations; i++) {
                const start = performance.now();
                window.dragDropSystem.discoverZones();
                const end = performance.now();
                durations.push(end - start);
            }

            const avg = durations.reduce((a, b) => a + b, 0) / iterations;
            const max = Math.max(...durations);

            return {
                avg: avg,
                max: max,
                min: Math.min(...durations)
            };
        """)

        print(f"\n=== discoverZones() Performance ===")
        print(f"Average: {result['avg']:.3f}ms")
        print(f"Max:     {result['max']:.3f}ms")
        print(f"Min:     {result['min']:.3f}ms")

        # Assertion: discoverZones() should be fast
        assert result['avg'] < 3, \
            f"discoverZones() average {result['avg']:.3f}ms exceeds 3ms target"
        assert result['max'] < 5, \
            f"discoverZones() max {result['max']:.3f}ms exceeds 5ms target"


class TestPerformanceBaseline:
    """
    Establish and validate performance baselines for regression detection.
    """

    def test_establish_baseline_metrics(self, setup_performance_test_page: Page):
        """
        Establish comprehensive baseline metrics for future regression detection.
        """
        page = setup_performance_test_page

        # Setup: Create realistic tag distribution
        page.evaluate("""
            const cloud = document.querySelector('.cloud-user .tags-wrapper');
            const includeZone = document.querySelector('[data-zone-type="include"]')?.querySelector('.tag-collection');
            const excludeZone = document.querySelector('[data-zone-type="exclude"]')?.querySelector('.tag-collection');

            // Create 1500 tags (realistic production load)
            for (let i = 0; i < 1500; i++) {
                const tag = document.createElement('span');
                tag.className = 'tag';
                tag.setAttribute('data-tag', `baseline-tag-${i}`);
                tag.setAttribute('data-tag-id', `baseline-id-${i}`);
                tag.setAttribute('draggable', 'true');
                tag.textContent = `baseline-tag-${i}`;

                // Realistic distribution: 60% cloud, 25% include, 15% exclude
                if (i < 900) {
                    tag.classList.add('tag-cloud');
                    cloud?.appendChild(tag);
                } else if (i < 1275) {
                    tag.classList.add('tag-active');
                    includeZone?.appendChild(tag);
                } else {
                    tag.classList.add('tag-active');
                    excludeZone?.appendChild(tag);
                }

                // 30% of tags are selected
                if (i % 10 < 3) {
                    tag.classList.add('tag-selected');
                }

                // 10% of tags are dragging
                if (i % 10 === 0) {
                    tag.classList.add('dragging');
                }
            }
        """)

        # Measure comprehensive baseline
        baseline = page.evaluate("""
            const measurements = {
                deriveStateFromDOM: [],
                discoverZones: [],
                getSelectedTags: [],
                getDraggedElements: []
            };

            // Run each operation 50 times
            for (let i = 0; i < 50; i++) {
                // deriveStateFromDOM
                let start = performance.now();
                window.dragDropSystem.deriveStateFromDOM();
                measurements.deriveStateFromDOM.push(performance.now() - start);

                // discoverZones
                start = performance.now();
                window.dragDropSystem.discoverZones();
                measurements.discoverZones.push(performance.now() - start);

                // Query selected tags (should use DOM, not JS variable)
                start = performance.now();
                document.querySelectorAll('[data-tag].tag-selected');
                measurements.getSelectedTags.push(performance.now() - start);

                // Query dragged elements (should use DOM, not JS array)
                start = performance.now();
                document.querySelectorAll('[data-tag].dragging');
                measurements.getDraggedElements.push(performance.now() - start);
            }

            // Calculate stats for each measurement
            const calculateStats = (arr) => {
                const sorted = arr.slice().sort((a, b) => a - b);
                const sum = arr.reduce((a, b) => a + b, 0);
                return {
                    avg: sum / arr.length,
                    median: sorted[Math.floor(arr.length / 2)],
                    p95: sorted[Math.floor(arr.length * 0.95)],
                    p99: sorted[Math.floor(arr.length * 0.99)],
                    max: Math.max(...arr),
                    min: Math.min(...arr)
                };
            };

            return {
                deriveStateFromDOM: calculateStats(measurements.deriveStateFromDOM),
                discoverZones: calculateStats(measurements.discoverZones),
                getSelectedTags: calculateStats(measurements.getSelectedTags),
                getDraggedElements: calculateStats(measurements.getDraggedElements)
            };
        """)

        print("\n=== PERFORMANCE BASELINE METRICS (1500 tags) ===")
        for operation, stats in baseline.items():
            print(f"\n{operation}:")
            print(f"  Average: {stats['avg']:.3f}ms")
            print(f"  Median:  {stats['median']:.3f}ms")
            print(f"  P95:     {stats['p95']:.3f}ms")
            print(f"  P99:     {stats['p99']:.3f}ms")
            print(f"  Max:     {stats['max']:.3f}ms")

        # Assertions: Baseline metrics should meet targets
        assert baseline['deriveStateFromDOM']['p95'] < 10, \
            f"deriveStateFromDOM P95 {baseline['deriveStateFromDOM']['p95']:.3f}ms exceeds 10ms"
        assert baseline['discoverZones']['p95'] < 5, \
            f"discoverZones P95 {baseline['discoverZones']['p95']:.3f}ms exceeds 5ms"
        assert baseline['getSelectedTags']['p95'] < 2, \
            f"getSelectedTags P95 {baseline['getSelectedTags']['p95']:.3f}ms exceeds 2ms"
        assert baseline['getDraggedElements']['p95'] < 2, \
            f"getDraggedElements P95 {baseline['getDraggedElements']['p95']:.3f}ms exceeds 2ms"

        # Store baseline for future regression detection
        with open('/tmp/dataos_performance_baseline.txt', 'w') as f:
            import json
            json.dump(baseline, f, indent=2)

        print("\nBaseline metrics saved to /tmp/dataos_performance_baseline.txt")


class TestRapidOperationPerformance:
    """
    Test performance during rapid operations without caching.
    """

    def test_rapid_selection_performance(self, setup_performance_test_page: Page):
        """
        Test that rapid selection operations maintain performance without caching.
        """
        page = setup_performance_test_page

        # Setup: Create 500 tags
        page.evaluate("""
            const cloud = document.querySelector('.cloud-user .tags-wrapper');
            for (let i = 0; i < 500; i++) {
                const tag = document.createElement('span');
                tag.className = 'tag tag-cloud';
                tag.setAttribute('data-tag', `rapid-tag-${i}`);
                tag.setAttribute('data-tag-id', `rapid-id-${i}`);
                tag.setAttribute('draggable', 'true');
                tag.textContent = `rapid-tag-${i}`;
                cloud?.appendChild(tag);
            }
        """)

        # Test: Rapidly select and deselect tags
        result = page.evaluate("""
            const tags = Array.from(document.querySelectorAll('[data-tag]'));
            const operations = 100;
            const durations = [];

            for (let i = 0; i < operations; i++) {
                const start = performance.now();

                // Select random tag
                const tag = tags[Math.floor(Math.random() * tags.length)];
                tag.classList.add('tag-selected');
                tag.setAttribute('aria-selected', 'true');

                // Query selection state (should use DOM, not cache)
                document.querySelectorAll('[data-tag].tag-selected');

                // Deselect
                tag.classList.remove('tag-selected');
                tag.setAttribute('aria-selected', 'false');

                durations.push(performance.now() - start);
            }

            const avg = durations.reduce((a, b) => a + b, 0) / operations;
            return {
                avg: avg,
                max: Math.max(...durations),
                allUnder1ms: durations.every(d => d < 1)
            };
        """)

        print(f"\n=== Rapid Selection Performance (100 ops) ===")
        print(f"Average: {result['avg']:.3f}ms per operation")
        print(f"Max:     {result['max']:.3f}ms")
        print(f"All ops <1ms: {result['allUnder1ms']}")

        # Assertion: Rapid operations should be sub-millisecond
        assert result['avg'] < 0.5, \
            f"Rapid selection average {result['avg']:.3f}ms exceeds 0.5ms"
        assert result['max'] < 2, \
            f"Rapid selection max {result['max']:.3f}ms exceeds 2ms"
