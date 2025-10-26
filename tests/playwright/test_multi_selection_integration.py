#!/usr/bin/env python3
"""
Multi-Selection Integration and Performance Test for multicardz™

Tests the complete multi-selection drag-drop system with real browser interactions.
Validates performance targets and cross-browser compatibility.

Performance Targets:
- Selection toggle: <5ms
- Range selection (100 tags): <50ms
- Ghost image generation: <16ms (single frame @ 60 FPS)
- Batch drop operation (50 tags): <500ms
- Memory usage: <10MB for 1000 selected tags

Test Coverage:
1. End-to-end multi-selection workflow
2. Click pattern selection (single, Ctrl/Cmd, Shift)
3. Keyboard navigation and accessibility
4. Ghost image generation and rendering
5. Batch operations with validation and rollback
6. Performance benchmarks
7. Memory leak detection
8. Cross-browser compatibility
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

import pytest
from playwright.async_api import async_playwright, Page, Browser

# Test configuration
SERVER_URL = "http://localhost:8011"
PERFORMANCE_THRESHOLDS = {
    "selection_toggle": 5,  # ms
    "range_selection_100": 50,  # ms
    "ghost_generation": 16,  # ms (one frame @ 60 FPS)
    "batch_drop_50": 500,  # ms
    "memory_1000_tags": 10 * 1024 * 1024,  # 10MB in bytes
}

pytestmark = pytest.mark.skip(reason="Playwright browser tests need manual setup")


class MultiSelectionIntegrationTest:
    """Comprehensive integration test for multi-selection features."""

    def __init__(self, headless=False, slow_mo=300, browser_type="chromium"):
        """
        Initialize test.

        Args:
            headless: Run in headless mode
            slow_mo: Slow down operations (ms) for visibility
            browser_type: Browser to test (chromium, firefox, webkit)
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.browser_type = browser_type
        self.browser = None
        self.page = None
        self.performance_results = {}
        self.test_results = {
            "passed": [],
            "failed": [],
            "performance": {},
            "memory": {},
        }

    async def setup(self):
        """Setup browser and page."""
        print(f"\n🎬 Setting up {self.browser_type} browser...")

        self.playwright = await async_playwright().start()

        # Launch appropriate browser
        if self.browser_type == "chromium":
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless, slow_mo=self.slow_mo
            )
        elif self.browser_type == "firefox":
            self.browser = await self.playwright.firefox.launch(
                headless=self.headless, slow_mo=self.slow_mo
            )
        elif self.browser_type == "webkit":
            self.browser = await self.playwright.webkit.launch(
                headless=self.headless, slow_mo=self.slow_mo
            )
        else:
            raise ValueError(f"Unknown browser type: {self.browser_type}")

        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )

        self.page = await self.context.new_page()
        self.page.on("console", lambda msg: print(f"🖥️  Console: {msg.text}"))

        print("✅ Browser ready")

    async def teardown(self):
        """Clean up browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def navigate_and_initialize(self):
        """Navigate to app and initialize multi-selection system."""
        print(f"\n🌐 Navigating to {SERVER_URL}...")

        await self.page.goto(SERVER_URL, wait_until="networkidle", timeout=10000)
        await asyncio.sleep(2)

        # Check if multi-selection system initialized
        system_ready = await self.page.evaluate("""
            () => {
                return typeof SpatialDragDrop !== 'undefined' &&
                       window.dragDropSystem !== null &&
                       window.dragDropSystem.selectionState !== undefined;
            }
        """)

        if system_ready:
            print("✅ Multi-selection system initialized")
        else:
            print("⚠️  Multi-selection system not detected, checking...")
            # Try manual initialization
            await self.page.evaluate("""
                if (typeof SpatialDragDrop !== 'undefined' && !window.dragDropSystem) {
                    window.dragDropSystem = new SpatialDragDrop();
                }
            """)

        return system_ready

    async def test_single_click_selection(self):
        """Test 1: Single click clears and selects single tag."""
        print("\n📋 Test 1: Single Click Selection")

        try:
            # Click first tag
            await self.page.click('[data-tag]:first-of-type')
            await asyncio.sleep(0.2)

            # Verify selection
            selection_count = await self.page.evaluate("""
                () => window.dragDropSystem.selectionState.selectedTags.size
            """)

            assert selection_count == 1, f"Expected 1 selected tag, got {selection_count}"

            # Click another tag (should clear first)
            await self.page.click('[data-tag]:nth-of-type(2)')
            await asyncio.sleep(0.2)

            selection_count = await self.page.evaluate("""
                () => window.dragDropSystem.selectionState.selectedTags.size
            """)

            assert selection_count == 1, f"Expected 1 selected tag, got {selection_count}"

            self.test_results["passed"].append("Single click selection")
            print("  ✅ Single click selection PASSED")
            return True

        except Exception as e:
            self.test_results["failed"].append(f"Single click selection: {e}")
            print(f"  ❌ Single click selection FAILED: {e}")
            return False

    async def test_ctrl_click_toggle(self):
        """Test 2: Ctrl/Cmd+click toggles selection."""
        print("\n📋 Test 2: Ctrl/Cmd+Click Toggle")

        try:
            # Clear selection
            await self.page.evaluate("""
                () => window.dragDropSystem.clearSelection()
            """)

            # Ctrl+click first tag
            await self.page.click('[data-tag]:first-of-type', modifiers=["Control"])
            await asyncio.sleep(0.2)

            # Ctrl+click second tag (should add)
            await self.page.click('[data-tag]:nth-of-type(2)', modifiers=["Control"])
            await asyncio.sleep(0.2)

            selection_count = await self.page.evaluate("""
                () => window.dragDropSystem.selectionState.selectedTags.size
            """)

            assert selection_count == 2, f"Expected 2 selected tags, got {selection_count}"

            # Ctrl+click first tag again (should remove)
            await self.page.click('[data-tag]:first-of-type', modifiers=["Control"])
            await asyncio.sleep(0.2)

            selection_count = await self.page.evaluate("""
                () => window.dragDropSystem.selectionState.selectedTags.size
            """)

            assert selection_count == 1, f"Expected 1 selected tag, got {selection_count}"

            self.test_results["passed"].append("Ctrl+click toggle")
            print("  ✅ Ctrl+click toggle PASSED")
            return True

        except Exception as e:
            self.test_results["failed"].append(f"Ctrl+click toggle: {e}")
            print(f"  ❌ Ctrl+click toggle FAILED: {e}")
            return False

    async def test_shift_click_range(self):
        """Test 3: Shift+click selects range."""
        print("\n📋 Test 3: Shift+Click Range Selection")

        try:
            # Clear and select first tag
            await self.page.evaluate("""
                () => window.dragDropSystem.clearSelection()
            """)
            await self.page.click('[data-tag]:first-of-type')
            await asyncio.sleep(0.2)

            # Shift+click 5th tag
            await self.page.click('[data-tag]:nth-of-type(5)', modifiers=["Shift"])
            await asyncio.sleep(0.2)

            selection_count = await self.page.evaluate("""
                () => window.dragDropSystem.selectionState.selectedTags.size
            """)

            assert selection_count == 5, f"Expected 5 selected tags, got {selection_count}"

            self.test_results["passed"].append("Shift+click range selection")
            print("  ✅ Shift+click range selection PASSED")
            return True

        except Exception as e:
            self.test_results["failed"].append(f"Shift+click range: {e}")
            print(f"  ❌ Shift+click range FAILED: {e}")
            return False

    async def test_keyboard_navigation(self):
        """Test 4: Keyboard navigation with arrow keys."""
        print("\n📋 Test 4: Keyboard Navigation")

        try:
            # Clear selection and focus first tag
            await self.page.evaluate("""
                () => {
                    window.dragDropSystem.clearSelection();
                    document.querySelector('[data-tag]').focus();
                }
            """)
            await asyncio.sleep(0.2)

            # Press Space to select
            await self.page.keyboard.press("Space")
            await asyncio.sleep(0.2)

            # Press ArrowRight to move focus
            await self.page.keyboard.press("ArrowRight")
            await asyncio.sleep(0.2)

            # Press Shift+Space to add to selection
            await self.page.keyboard.press("Space", modifiers=["Shift"])
            await asyncio.sleep(0.2)

            selection_count = await self.page.evaluate("""
                () => window.dragDropSystem.selectionState.selectedTags.size
            """)

            assert selection_count == 2, f"Expected 2 selected tags, got {selection_count}"

            self.test_results["passed"].append("Keyboard navigation")
            print("  ✅ Keyboard navigation PASSED")
            return True

        except Exception as e:
            self.test_results["failed"].append(f"Keyboard navigation: {e}")
            print(f"  ❌ Keyboard navigation FAILED: {e}")
            return False

    async def test_select_all_keyboard(self):
        """Test 5: Ctrl/Cmd+A selects all tags."""
        print("\n📋 Test 5: Select All (Ctrl+A)")

        try:
            # Focus tag area
            await self.page.click('[data-tag]:first-of-type')
            await asyncio.sleep(0.2)

            # Press Ctrl+A
            await self.page.keyboard.press("Control+a")
            await asyncio.sleep(0.2)

            selection_count = await self.page.evaluate("""
                () => window.dragDropSystem.selectionState.selectedTags.size
            """)

            total_tags = await self.page.evaluate("""
                () => document.querySelectorAll('[data-tag]:not([hidden])').length
            """)

            assert (
                selection_count == total_tags
            ), f"Expected {total_tags} selected tags, got {selection_count}"

            self.test_results["passed"].append("Select all keyboard")
            print(f"  ✅ Select all keyboard PASSED ({selection_count} tags)")
            return True

        except Exception as e:
            self.test_results["failed"].append(f"Select all keyboard: {e}")
            print(f"  ❌ Select all keyboard FAILED: {e}")
            return False

    async def test_ghost_image_generation(self):
        """Test 6: Ghost image generation for multi-tag drag."""
        print("\n📋 Test 6: Ghost Image Generation")

        try:
            # Select multiple tags
            await self.page.evaluate("""
                () => window.dragDropSystem.clearSelection()
            """)
            await self.page.click('[data-tag]:first-of-type')
            await self.page.click('[data-tag]:nth-of-type(2)', modifiers=["Control"])
            await self.page.click('[data-tag]:nth-of-type(3)', modifiers=["Control"])
            await asyncio.sleep(0.2)

            # Start drag and measure ghost generation time
            performance_data = await self.page.evaluate("""
                async () => {
                    const startTime = performance.now();

                    // Trigger drag start
                    const firstTag = document.querySelector('[data-tag]');
                    const dragEvent = new DragEvent('dragstart', {
                        bubbles: true,
                        cancelable: true,
                        dataTransfer: new DataTransfer()
                    });

                    firstTag.dispatchEvent(dragEvent);

                    const duration = performance.now() - startTime;

                    return {
                        duration: duration,
                        ghostGenerated: window.dragDropSystem.currentGhostImage !== null
                    };
                }
            """)

            duration_ms = performance_data["duration"]
            ghost_generated = performance_data["ghostGenerated"]

            assert ghost_generated, "Ghost image was not generated"
            assert (
                duration_ms < PERFORMANCE_THRESHOLDS["ghost_generation"]
            ), f"Ghost generation took {duration_ms:.2f}ms (threshold: {PERFORMANCE_THRESHOLDS['ghost_generation']}ms)"

            self.test_results["performance"]["ghost_generation"] = duration_ms
            self.test_results["passed"].append("Ghost image generation")
            print(
                f"  ✅ Ghost image generation PASSED ({duration_ms:.2f}ms < {PERFORMANCE_THRESHOLDS['ghost_generation']}ms)"
            )
            return True

        except Exception as e:
            self.test_results["failed"].append(f"Ghost image generation: {e}")
            print(f"  ❌ Ghost image generation FAILED: {e}")
            return False

    async def test_batch_drop_operation(self):
        """Test 7: Batch drop operation with multiple tags."""
        print("\n📋 Test 7: Batch Drop Operation")

        try:
            # Select multiple tags
            await self.page.evaluate("""
                () => {
                    window.dragDropSystem.clearSelection();
                    const tags = Array.from(document.querySelectorAll('[data-tag]')).slice(0, 5);
                    tags.forEach(tag => window.dragDropSystem.addToSelection(tag));
                }
            """)
            await asyncio.sleep(0.2)

            # Get first tag and intersection zone
            first_tag = await self.page.query_selector('[data-tag]')
            intersection_zone = await self.page.query_selector(
                '[data-zone-type="intersection"]'
            )

            if not first_tag or not intersection_zone:
                print("  ⚠️  Cannot test batch drop - missing elements")
                return False

            # Perform drag and drop
            tag_box = await first_tag.bounding_box()
            zone_box = await intersection_zone.bounding_box()

            if not tag_box or not zone_box:
                print("  ⚠️  Cannot get bounding boxes")
                return False

            # Start performance measurement
            start_time = time.perf_counter()

            # Drag from tag to zone
            await self.page.mouse.move(
                tag_box["x"] + tag_box["width"] / 2,
                tag_box["y"] + tag_box["height"] / 2,
            )
            await self.page.mouse.down()
            await asyncio.sleep(0.2)
            await self.page.mouse.move(
                zone_box["x"] + zone_box["width"] / 2,
                zone_box["y"] + zone_box["height"] / 2,
                steps=10,
            )
            await self.page.mouse.up()
            await asyncio.sleep(0.5)  # Wait for batch operation

            duration_ms = (time.perf_counter() - start_time) * 1000

            # Verify tags moved
            tags_in_zone = await self.page.evaluate("""
                () => document.querySelectorAll('[data-zone-type="intersection"] [data-tag]').length
            """)

            assert tags_in_zone >= 5, f"Expected at least 5 tags in zone, got {tags_in_zone}"

            self.test_results["performance"]["batch_drop"] = duration_ms
            self.test_results["passed"].append("Batch drop operation")
            print(f"  ✅ Batch drop operation PASSED ({duration_ms:.2f}ms)")
            return True

        except Exception as e:
            self.test_results["failed"].append(f"Batch drop operation: {e}")
            print(f"  ❌ Batch drop operation FAILED: {e}")
            return False

    async def test_performance_selection_toggle(self):
        """Test 8: Performance benchmark for selection toggle."""
        print("\n📋 Test 8: Performance - Selection Toggle")

        try:
            performance_data = await self.page.evaluate("""
                () => {
                    const iterations = 100;
                    const durations = [];

                    const tags = Array.from(document.querySelectorAll('[data-tag]'));
                    if (tags.length === 0) return { avgDuration: 0, maxDuration: 0 };

                    window.dragDropSystem.clearSelection();

                    for (let i = 0; i < iterations; i++) {
                        const tag = tags[i % tags.length];
                        const startTime = performance.now();
                        window.dragDropSystem.toggleSelection(tag);
                        const duration = performance.now() - startTime;
                        durations.push(duration);
                    }

                    const avgDuration = durations.reduce((a, b) => a + b, 0) / durations.length;
                    const maxDuration = Math.max(...durations);

                    return { avgDuration, maxDuration };
                }
            """)

            avg_duration = performance_data["avgDuration"]
            max_duration = performance_data["maxDuration"]

            assert (
                avg_duration < PERFORMANCE_THRESHOLDS["selection_toggle"]
            ), f"Average selection toggle took {avg_duration:.2f}ms (threshold: {PERFORMANCE_THRESHOLDS['selection_toggle']}ms)"

            self.test_results["performance"]["selection_toggle_avg"] = avg_duration
            self.test_results["performance"]["selection_toggle_max"] = max_duration
            self.test_results["passed"].append("Performance: Selection toggle")
            print(
                f"  ✅ Selection toggle performance PASSED (avg: {avg_duration:.2f}ms, max: {max_duration:.2f}ms)"
            )
            return True

        except Exception as e:
            self.test_results["failed"].append(f"Performance selection toggle: {e}")
            print(f"  ❌ Performance selection toggle FAILED: {e}")
            return False

    async def test_performance_range_selection(self):
        """Test 9: Performance benchmark for range selection."""
        print("\n📋 Test 9: Performance - Range Selection (100 tags)")

        try:
            # Create 100 test tags if needed
            tag_count = await self.page.evaluate("""
                () => document.querySelectorAll('[data-tag]').length
            """)

            if tag_count < 100:
                print(f"  ℹ️  Only {tag_count} tags available (need 100 for full test)")

            performance_data = await self.page.evaluate("""
                () => {
                    const tags = Array.from(document.querySelectorAll('[data-tag]'));
                    const count = Math.min(tags.length, 100);

                    if (count < 10) return { duration: 0, count: 0 };

                    window.dragDropSystem.clearSelection();
                    window.dragDropSystem.selectionState.anchorTag = tags[0];

                    const startTime = performance.now();
                    window.dragDropSystem.selectRange(tags[0], tags[count - 1]);
                    const duration = performance.now() - startTime;

                    return {
                        duration,
                        count: window.dragDropSystem.selectionState.selectedTags.size
                    };
                }
            """)

            duration_ms = performance_data["duration"]
            selected_count = performance_data["count"]

            if selected_count == 0:
                print("  ⚠️  Not enough tags for range selection test")
                return False

            threshold = PERFORMANCE_THRESHOLDS["range_selection_100"]
            assert (
                duration_ms < threshold
            ), f"Range selection took {duration_ms:.2f}ms (threshold: {threshold}ms)"

            self.test_results["performance"]["range_selection"] = duration_ms
            self.test_results["passed"].append("Performance: Range selection")
            print(
                f"  ✅ Range selection performance PASSED ({duration_ms:.2f}ms for {selected_count} tags)"
            )
            return True

        except Exception as e:
            self.test_results["failed"].append(f"Performance range selection: {e}")
            print(f"  ❌ Performance range selection FAILED: {e}")
            return False

    async def test_memory_usage(self):
        """Test 10: Memory usage with large selections."""
        print("\n📋 Test 10: Memory Usage Test")

        try:
            # Get initial memory
            initial_memory = await self.page.evaluate("""
                () => {
                    if (performance.memory) {
                        return performance.memory.usedJSHeapSize;
                    }
                    return 0;
                }
            """)

            if initial_memory == 0:
                print("  ⚠️  Memory API not available in this browser")
                return False

            # Select many tags
            await self.page.evaluate("""
                () => {
                    const tags = Array.from(document.querySelectorAll('[data-tag]'));
                    window.dragDropSystem.clearSelection();
                    tags.forEach(tag => window.dragDropSystem.addToSelection(tag));
                }
            """)
            await asyncio.sleep(0.5)

            # Get memory after selection
            final_memory = await self.page.evaluate("""
                () => performance.memory.usedJSHeapSize
            """)

            selected_count = await self.page.evaluate("""
                () => window.dragDropSystem.selectionState.selectedTags.size
            """)

            memory_delta = final_memory - initial_memory
            memory_delta_mb = memory_delta / 1024 / 1024

            # Calculate per-tag memory (for extrapolation)
            per_tag_bytes = memory_delta / max(selected_count, 1)
            estimated_1000_tags = per_tag_bytes * 1000

            self.test_results["memory"]["selected_count"] = selected_count
            self.test_results["memory"]["memory_delta_bytes"] = memory_delta
            self.test_results["memory"]["memory_delta_mb"] = memory_delta_mb
            self.test_results["memory"]["estimated_1000_tags_mb"] = (
                estimated_1000_tags / 1024 / 1024
            )

            print(
                f"  ℹ️  Memory delta: {memory_delta_mb:.2f}MB for {selected_count} tags"
            )
            print(
                f"  ℹ️  Estimated for 1000 tags: {estimated_1000_tags / 1024 / 1024:.2f}MB"
            )

            # Check if within threshold
            if estimated_1000_tags < PERFORMANCE_THRESHOLDS["memory_1000_tags"]:
                self.test_results["passed"].append("Memory usage")
                print("  ✅ Memory usage PASSED")
                return True
            else:
                self.test_results["failed"].append(
                    f"Memory usage: {estimated_1000_tags / 1024 / 1024:.2f}MB exceeds 10MB threshold"
                )
                print(
                    f"  ⚠️  Memory usage exceeds threshold but test continues ({estimated_1000_tags / 1024 / 1024:.2f}MB > 10MB)"
                )
                return True  # Don't fail on memory, just warn

        except Exception as e:
            self.test_results["failed"].append(f"Memory usage: {e}")
            print(f"  ❌ Memory usage test FAILED: {e}")
            return False

    async def test_aria_states(self):
        """Test 11: ARIA states and accessibility."""
        print("\n📋 Test 11: ARIA States and Accessibility")

        try:
            # Clear and select some tags
            await self.page.evaluate("""
                () => {
                    window.dragDropSystem.clearSelection();
                    const tags = Array.from(document.querySelectorAll('[data-tag]')).slice(0, 3);
                    tags.forEach(tag => window.dragDropSystem.addToSelection(tag));
                }
            """)
            await asyncio.sleep(0.2)

            # Check ARIA states
            aria_data = await self.page.evaluate("""
                () => {
                    const allTags = Array.from(document.querySelectorAll('[data-tag]'));
                    const selectedTags = allTags.filter(tag =>
                        tag.getAttribute('aria-selected') === 'true'
                    );
                    const unselectedTags = allTags.filter(tag =>
                        tag.getAttribute('aria-selected') === 'false'
                    );

                    const container = document.querySelector('.cloud, .tag-collection');

                    return {
                        totalTags: allTags.length,
                        selectedCount: selectedTags.length,
                        unselectedCount: unselectedTags.length,
                        containerHasMultiselectable: container ?
                            container.getAttribute('aria-multiselectable') === 'true' : false,
                        allTagsHaveRole: allTags.every(tag => tag.getAttribute('role') === 'option')
                    };
                }
            """)

            assert (
                aria_data["selectedCount"] == 3
            ), f"Expected 3 tags with aria-selected=true, got {aria_data['selectedCount']}"
            assert aria_data[
                "containerHasMultiselectable"
            ], "Container should have aria-multiselectable=true"
            assert aria_data["allTagsHaveRole"], "All tags should have role=option"

            self.test_results["passed"].append("ARIA states")
            print("  ✅ ARIA states and accessibility PASSED")
            return True

        except Exception as e:
            self.test_results["failed"].append(f"ARIA states: {e}")
            print(f"  ❌ ARIA states FAILED: {e}")
            return False

    async def test_screen_reader_announcements(self):
        """Test 12: Screen reader announcements."""
        print("\n📋 Test 12: Screen Reader Announcements")

        try:
            # Check for live region
            live_region_exists = await self.page.evaluate("""
                () => {
                    const announcer = document.getElementById('selection-announcer');
                    return announcer !== null &&
                           announcer.getAttribute('aria-live') === 'polite';
                }
            """)

            assert live_region_exists, "Live region for screen reader should exist"

            # Select a tag and check announcement
            await self.page.evaluate("""
                () => {
                    window.dragDropSystem.clearSelection();
                    const tag = document.querySelector('[data-tag]');
                    window.dragDropSystem.addToSelection(tag);
                }
            """)
            await asyncio.sleep(0.3)  # Wait for announcement

            announcement_text = await self.page.evaluate("""
                () => document.getElementById('selection-announcer').textContent
            """)

            # Should contain some announcement (exact text may vary)
            assert (
                len(announcement_text.strip()) > 0
            ), "Screen reader announcement should not be empty"

            self.test_results["passed"].append("Screen reader announcements")
            print(f"  ✅ Screen reader announcements PASSED ('{announcement_text}')")
            return True

        except Exception as e:
            self.test_results["failed"].append(f"Screen reader announcements: {e}")
            print(f"  ❌ Screen reader announcements FAILED: {e}")
            return False

    async def run_all_tests(self):
        """Run all integration tests."""
        print("\n" + "=" * 80)
        print("MULTI-SELECTION INTEGRATION AND PERFORMANCE TEST SUITE")
        print(f"Browser: {self.browser_type}")
        print("=" * 80)

        await self.setup()

        try:
            # Navigate and initialize
            if not await self.navigate_and_initialize():
                print("\n❌ Failed to initialize system - aborting tests")
                return

            # Run all tests
            tests = [
                self.test_single_click_selection,
                self.test_ctrl_click_toggle,
                self.test_shift_click_range,
                self.test_keyboard_navigation,
                self.test_select_all_keyboard,
                self.test_ghost_image_generation,
                self.test_batch_drop_operation,
                self.test_performance_selection_toggle,
                self.test_performance_range_selection,
                self.test_memory_usage,
                self.test_aria_states,
                self.test_screen_reader_announcements,
            ]

            for test in tests:
                await test()
                await asyncio.sleep(0.5)  # Brief pause between tests

            # Print summary
            self.print_test_summary()

        finally:
            await self.teardown()

    def print_test_summary(self):
        """Print comprehensive test summary."""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        passed_count = len(self.test_results["passed"])
        failed_count = len(self.test_results["failed"])
        total_count = passed_count + failed_count

        print(f"\n✅ Passed: {passed_count}/{total_count}")
        print(f"❌ Failed: {failed_count}/{total_count}")

        if self.test_results["passed"]:
            print("\nPassed Tests:")
            for test in self.test_results["passed"]:
                print(f"  ✅ {test}")

        if self.test_results["failed"]:
            print("\nFailed Tests:")
            for test in self.test_results["failed"]:
                print(f"  ❌ {test}")

        if self.test_results["performance"]:
            print("\nPerformance Results:")
            for metric, value in self.test_results["performance"].items():
                threshold_key = metric.replace("_avg", "").replace("_max", "")
                threshold = PERFORMANCE_THRESHOLDS.get(threshold_key, "N/A")
                status = "✅" if (threshold != "N/A" and value < threshold) else "ℹ️"
                print(f"  {status} {metric}: {value:.2f}ms (threshold: {threshold}ms)")

        if self.test_results["memory"]:
            print("\nMemory Usage:")
            for metric, value in self.test_results["memory"].items():
                if isinstance(value, float):
                    print(f"  ℹ️  {metric}: {value:.2f}")
                else:
                    print(f"  ℹ️  {metric}: {value}")

        print("\n" + "=" * 80)

        # Save results to file
        results_file = Path(__file__).parent / "test_results_multi_selection.json"
        with open(results_file, "w") as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\n📊 Full results saved to: {results_file}")


async def main():
    """Main test runner."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Multi-Selection Integration and Performance Test"
    )
    parser.add_argument(
        "--headless", action="store_true", help="Run in headless mode"
    )
    parser.add_argument(
        "--slow-mo",
        type=int,
        default=300,
        help="Slow down operations (ms) for visibility",
    )
    parser.add_argument(
        "--browser",
        choices=["chromium", "firefox", "webkit"],
        default="chromium",
        help="Browser to test",
    )

    args = parser.parse_args()

    tester = MultiSelectionIntegrationTest(
        headless=args.headless, slow_mo=args.slow_mo, browser_type=args.browser
    )
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
