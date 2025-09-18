#!/usr/bin/env python3
"""
Comprehensive Responsive & Window Resizing Test for MultiCardz™.
Tests that the UI adapts properly to different viewport sizes and window resizing.

Key Test Areas:
1. Card display area maximization within available viewport
2. UI controls repositioning and scaling
3. Tag cloud responsiveness
4. Zone layout adaptation
5. Typography and spacing at different sizes
6. Touch-friendly sizing on mobile viewports
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

from playwright.async_api import async_playwright, expect

# Add apps to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))


class ResponsiveTestSuite:
    """Comprehensive responsive behavior testing."""

    def __init__(self, headless=False, slow_mo=100):
        """
        Initialize responsive tester.

        Args:
            headless: Run in headless mode
            slow_mo: Slow down operations (ms) for visibility
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.browser = None
        self.page = None
        self.test_results = []

        # Standard test viewports
        self.test_viewports = [
            {"name": "Mobile Portrait", "width": 375, "height": 667},      # iPhone SE
            {"name": "Mobile Landscape", "width": 667, "height": 375},     # iPhone SE landscape
            {"name": "Tablet Portrait", "width": 768, "height": 1024},     # iPad
            {"name": "Tablet Landscape", "width": 1024, "height": 768},    # iPad landscape
            {"name": "Desktop Small", "width": 1280, "height": 720},       # Small desktop
            {"name": "Desktop Medium", "width": 1440, "height": 900},      # Medium desktop
            {"name": "Desktop Large", "width": 1920, "height": 1080},      # Full HD
            {"name": "Desktop XL", "width": 2560, "height": 1440},         # 2K
            {"name": "Ultrawide", "width": 3440, "height": 1440},          # Ultrawide monitor
        ]

    async def setup(self):
        """Setup browser and page for responsive testing."""
        print("🎬 Setting up Responsive Testing Environment...")

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )

        # Start with a standard desktop viewport
        self.context = await self.browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )

        self.page = await self.context.new_page()

        # Enable console logging
        self.page.on("console", lambda msg: print(f"🖥️  Console [{msg.type}]: {msg.text}"))
        self.page.on("pageerror", lambda err: print(f"❌ Page Error: {err}"))

        print("✅ Responsive testing environment ready")

    async def teardown(self):
        """Clean up browser resources."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def record_test_result(self, test_name: str, viewport: str, success: bool,
                          duration: float, measurements: Dict = None):
        """Record test result with viewport context."""
        self.test_results.append({
            "test": test_name,
            "viewport": viewport,
            "success": success,
            "duration": duration,
            "measurements": measurements or {},
            "timestamp": time.time()
        })

    async def navigate_to_production_app(self, url="http://localhost:8001"):
        """Navigate to the real MultiCardz production app."""
        print(f"🌐 Loading production app: {url}")

        try:
            await self.page.goto(url, wait_until="networkidle", timeout=15000)
            await asyncio.sleep(2)  # Wait for initialization

            # Verify system is ready
            system_ready = await self.page.evaluate("""
                () => {
                    return typeof SpatialDragDrop !== 'undefined' &&
                           window.dragDropSystem !== null &&
                           document.querySelectorAll('.tag').length > 0 &&
                           document.querySelectorAll('.drop-zone').length > 0;
                }
            """)

            if system_ready:
                print("✅ Production app loaded and initialized")
                return True
            else:
                print("⚠️  System not fully ready")
                return False

        except Exception as e:
            print(f"❌ Failed to load app: {e}")
            return False

    async def measure_viewport_utilization(self, viewport_name: str) -> Dict:
        """Measure how well the UI utilizes the available viewport."""
        measurements = {}

        try:
            # Get viewport dimensions
            viewport_info = await self.page.evaluate("""
                () => ({
                    innerWidth: window.innerWidth,
                    innerHeight: window.innerHeight,
                    outerWidth: window.outerWidth,
                    outerHeight: window.outerHeight
                })
            """)

            # Measure card display area
            card_display_info = await self.page.evaluate("""
                () => {
                    const cardContainer = document.querySelector('.card-display');
                    if (!cardContainer) return null;

                    const rect = cardContainer.getBoundingClientRect();
                    return {
                        width: rect.width,
                        height: rect.height,
                        top: rect.top,
                        left: rect.left,
                        right: rect.right,
                        bottom: rect.bottom,
                        visibleArea: rect.width * rect.height
                    };
                }
            """)

            # Measure spatial grid utilization
            grid_info = await self.page.evaluate("""
                () => {
                    const grid = document.querySelector('.spatial-grid');
                    if (!grid) return null;

                    const rect = grid.getBoundingClientRect();
                    return {
                        width: rect.width,
                        height: rect.height,
                        utilizationPercent: (rect.width * rect.height) / (window.innerWidth * window.innerHeight) * 100
                    };
                }
            """)

            # Calculate utilization metrics
            if card_display_info and viewport_info:
                viewport_area = viewport_info['innerWidth'] * viewport_info['innerHeight']
                card_utilization = (card_display_info['visibleArea'] / viewport_area) * 100

                measurements = {
                    "viewport": viewport_info,
                    "card_display": card_display_info,
                    "grid": grid_info,
                    "card_utilization_percent": card_utilization,
                    "viewport_efficiency": "excellent" if card_utilization > 40 else
                                         "good" if card_utilization > 25 else
                                         "poor" if card_utilization > 15 else "critical"
                }

            print(f"📏 {viewport_name} - Card area utilization: {measurements.get('card_utilization_percent', 0):.1f}%")

        except Exception as e:
            print(f"⚠️  Measurement error: {e}")

        return measurements

    async def test_viewport_resize_sequence(self):
        """Test resizing through a sequence of viewports to ensure smooth adaptation."""
        print("\\n🧪 Testing Viewport Resize Sequence")
        print("=" * 60)

        # Start with desktop and resize to each viewport
        for i, viewport in enumerate(self.test_viewports):
            start_time = time.time()
            viewport_name = f"{viewport['name']} ({viewport['width']}x{viewport['height']})"

            try:
                print(f"\\n🔄 Resizing to: {viewport_name}")

                # Resize viewport
                await self.page.set_viewport_size({"width": viewport['width'], "height": viewport['height']})
                await asyncio.sleep(0.5)  # Allow CSS transitions to complete

                # Wait for any responsive behavior to settle
                await self.page.wait_for_timeout(200)

                # Measure utilization
                measurements = await self.measure_viewport_utilization(viewport_name)

                # Test drag-drop still works at this size
                drag_test_success = await self.test_drag_drop_at_current_size()

                # Check for layout issues
                layout_issues = await self.detect_layout_issues()

                duration = time.time() - start_time
                success = len(layout_issues) == 0 and drag_test_success

                self.record_test_result(
                    f"Viewport Resize {i+1}",
                    viewport_name,
                    success,
                    duration,
                    {**measurements, "drag_test": drag_test_success, "layout_issues": layout_issues}
                )

                if layout_issues:
                    print(f"  ⚠️  Layout issues: {layout_issues}")
                else:
                    print(f"  ✅ Layout adapts properly")

            except Exception as e:
                duration = time.time() - start_time
                print(f"  ❌ Failed: {e}")
                self.record_test_result(f"Viewport Resize {i+1}", viewport_name, False, duration)

    async def test_drag_drop_at_current_size(self) -> bool:
        """Test that drag-drop still works at the current viewport size."""
        try:
            # Find any available tag and zone
            tag_selector = ".tag-user[data-tag]:first-child"
            zone_selector = ".union-zone"

            tag_exists = await self.page.query_selector(tag_selector)
            zone_exists = await self.page.query_selector(zone_selector)

            if not tag_exists or not zone_exists:
                return False

            # Get positions
            tag_box = await tag_exists.bounding_box()
            zone_box = await zone_exists.bounding_box()

            if not tag_box or not zone_box:
                return False

            # Quick drag test
            source_x = tag_box["x"] + tag_box["width"] / 2
            source_y = tag_box["y"] + tag_box["height"] / 2
            target_x = zone_box["x"] + zone_box["width"] / 2
            target_y = zone_box["y"] + zone_box["height"] / 2

            await self.page.mouse.move(source_x, source_y)
            await self.page.mouse.down()
            await self.page.mouse.move(target_x, target_y)
            await self.page.mouse.up()

            await asyncio.sleep(0.1)
            return True

        except Exception:
            return False

    async def detect_layout_issues(self) -> List[str]:
        """Detect common layout issues at current viewport size."""
        issues = []

        try:
            layout_checks = await self.page.evaluate("""
                () => {
                    const issues = [];

                    // Check for horizontal overflow
                    if (document.body.scrollWidth > window.innerWidth) {
                        issues.push('horizontal_overflow');
                    }

                    // Check for elements outside viewport
                    document.querySelectorAll('.tag, .drop-zone, .control-area-container').forEach(el => {
                        const rect = el.getBoundingClientRect();
                        if (rect.right > window.innerWidth || rect.bottom > window.innerHeight) {
                            issues.push('elements_outside_viewport');
                        }
                    });

                    // Check for overlapping elements
                    const zones = document.querySelectorAll('.drop-zone');
                    for (let i = 0; i < zones.length; i++) {
                        const rect1 = zones[i].getBoundingClientRect();
                        for (let j = i + 1; j < zones.length; j++) {
                            const rect2 = zones[j].getBoundingClientRect();
                            if (rect1.left < rect2.right && rect2.left < rect1.right &&
                                rect1.top < rect2.bottom && rect2.top < rect1.bottom) {
                                issues.push('overlapping_zones');
                                break;
                            }
                        }
                    }

                    // Check minimum touch target sizes (44px recommended)
                    document.querySelectorAll('.tag, button, input').forEach(el => {
                        const rect = el.getBoundingClientRect();
                        if (rect.width < 44 || rect.height < 44) {
                            issues.push('small_touch_targets');
                        }
                    });

                    // Check card display area visibility
                    const cardDisplay = document.querySelector('.card-display');
                    if (cardDisplay) {
                        const rect = cardDisplay.getBoundingClientRect();
                        if (rect.width < 200 || rect.height < 200) {
                            issues.push('card_area_too_small');
                        }
                    }

                    return [...new Set(issues)]; // Remove duplicates
                }
            """)

            issues = layout_checks

        except Exception as e:
            issues = [f"detection_error: {e}"]

        return issues

    async def test_card_display_maximization(self):
        """Test that the card display area maximizes available space efficiently."""
        print("\\n🧪 Testing Card Display Maximization")
        print("=" * 60)

        for viewport in self.test_viewports:
            viewport_name = f"{viewport['name']} ({viewport['width']}x{viewport['height']})"
            start_time = time.time()

            try:
                await self.page.set_viewport_size({"width": viewport['width'], "height": viewport['height']})
                await asyncio.sleep(0.3)

                # Measure card display utilization
                measurements = await self.measure_viewport_utilization(viewport_name)
                utilization = measurements.get('card_utilization_percent', 0)

                # Check if maximization is appropriate for viewport type
                if viewport['width'] >= 1280:  # Desktop
                    success = utilization >= 30  # Expect at least 30% utilization on desktop
                elif viewport['width'] >= 768:   # Tablet
                    success = utilization >= 25  # Expect at least 25% on tablet
                else:  # Mobile
                    success = utilization >= 20  # Expect at least 20% on mobile

                duration = time.time() - start_time

                self.record_test_result(
                    "Card Display Maximization",
                    viewport_name,
                    success,
                    duration,
                    measurements
                )

                efficiency = measurements.get('viewport_efficiency', 'unknown')
                print(f"  📊 {viewport_name}: {utilization:.1f}% utilization ({efficiency})")

            except Exception as e:
                duration = time.time() - start_time
                print(f"  ❌ {viewport_name}: Failed - {e}")
                self.record_test_result("Card Display Maximization", viewport_name, False, duration)

    async def test_dynamic_resizing_behavior(self):
        """Test behavior during live window resizing."""
        print("\\n🧪 Testing Dynamic Resizing Behavior")
        print("=" * 60)

        start_viewport = {"width": 1920, "height": 1080}
        end_viewport = {"width": 375, "height": 667}

        try:
            # Start large
            await self.page.set_viewport_size({"width": start_viewport['width'], "height": start_viewport['height']})
            await asyncio.sleep(0.5)

            # Populate some zones with content for testing
            await self.populate_test_content()

            # Gradually resize in steps
            steps = 10
            start_time = time.time()

            for i in range(steps + 1):
                progress = i / steps
                current_width = start_viewport['width'] + (end_viewport['width'] - start_viewport['width']) * progress
                current_height = start_viewport['height'] + (end_viewport['height'] - start_viewport['height']) * progress

                await self.page.set_viewport_size({"width": int(current_width), "height": int(current_height)})
                await asyncio.sleep(0.1)  # Brief pause between steps

                # Check for issues during resize
                if i % 3 == 0:  # Check every 3rd step
                    issues = await self.detect_layout_issues()
                    if issues:
                        print(f"  ⚠️  Issues at {int(current_width)}x{int(current_height)}: {issues}")

            duration = time.time() - start_time

            # Final measurement
            final_measurements = await self.measure_viewport_utilization("Mobile Final")
            final_issues = await self.detect_layout_issues()

            success = len(final_issues) == 0

            self.record_test_result(
                "Dynamic Resizing",
                f"{start_viewport['width']}x{start_viewport['height']} → {end_viewport['width']}x{end_viewport['height']}",
                success,
                duration,
                {**final_measurements, "final_issues": final_issues}
            )

            print(f"  📱 Resize sequence: {'✅ Smooth' if success else '⚠️  Issues detected'}")

        except Exception as e:
            print(f"  ❌ Dynamic resize test failed: {e}")

    async def populate_test_content(self):
        """Add some test content to zones for better resize testing."""
        try:
            # Drag a few tags to zones to create content
            test_moves = [
                (".tag-user[data-tag]:nth-child(1)", ".union-zone"),
                (".tag-user[data-tag]:nth-child(2)", ".intersection-zone"),
            ]

            for source, target in test_moves:
                source_el = await self.page.query_selector(source)
                target_el = await self.page.query_selector(target)

                if source_el and target_el:
                    source_box = await source_el.bounding_box()
                    target_box = await target_el.bounding_box()

                    if source_box and target_box:
                        await self.page.mouse.move(
                            source_box["x"] + source_box["width"] / 2,
                            source_box["y"] + source_box["height"] / 2
                        )
                        await self.page.mouse.down()
                        await self.page.mouse.move(
                            target_box["x"] + target_box["width"] / 2,
                            target_box["y"] + target_box["height"] / 2
                        )
                        await self.page.mouse.up()
                        await asyncio.sleep(0.2)

        except Exception as e:
            print(f"  ⚠️  Could not populate test content: {e}")

    async def take_responsive_screenshots(self):
        """Take screenshots at different viewport sizes."""
        print("\\n📸 Taking Responsive Screenshots")
        print("=" * 60)

        screenshot_viewports = [
            {"name": "mobile", "width": 375, "height": 667},
            {"name": "tablet", "width": 768, "height": 1024},
            {"name": "desktop", "width": 1440, "height": 900},
            {"name": "ultrawide", "width": 3440, "height": 1440},
        ]

        for viewport in screenshot_viewports:
            try:
                await self.page.set_viewport_size({"width": viewport['width'], "height": viewport['height']})
                await asyncio.sleep(0.5)

                filename = f"responsive_{viewport['name']}_{viewport['width']}x{viewport['height']}.png"
                await self.page.screenshot(path=f"tests/artifacts/{filename}", full_page=True)
                print(f"  📷 {filename}")

            except Exception as e:
                print(f"  ⚠️  Screenshot failed for {viewport['name']}: {e}")

    def generate_responsive_report(self):
        """Generate comprehensive responsive testing report."""
        print("\\n📊 Responsive Testing Report")
        print("=" * 60)

        if not self.test_results:
            print("No test results to report")
            return False

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests

        # Group by test type
        test_types = {}
        viewport_performance = {}

        for result in self.test_results:
            test_type = result["test"]
            viewport = result["viewport"]

            if test_type not in test_types:
                test_types[test_type] = {"passed": 0, "failed": 0, "total": 0}

            test_types[test_type]["total"] += 1
            if result["success"]:
                test_types[test_type]["passed"] += 1
            else:
                test_types[test_type]["failed"] += 1

            # Track viewport utilization
            measurements = result.get("measurements", {})
            utilization = measurements.get("card_utilization_percent")
            if utilization is not None:
                if viewport not in viewport_performance:
                    viewport_performance[viewport] = []
                viewport_performance[viewport].append(utilization)

        print(f"📈 Overall Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   📊 Success Rate: {(passed_tests/total_tests*100):.1f}%")

        print(f"\\n📋 Test Type Breakdown:")
        for test_type, stats in test_types.items():
            success_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"   {test_type}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")

        print(f"\\n📐 Viewport Utilization Analysis:")
        for viewport, utilizations in viewport_performance.items():
            if utilizations:
                avg_util = sum(utilizations) / len(utilizations)
                print(f"   {viewport}: {avg_util:.1f}% average")

        # Save detailed report
        report_data = {
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": passed_tests/total_tests if total_tests > 0 else 0
            },
            "test_types": test_types,
            "viewport_performance": viewport_performance,
            "detailed_results": self.test_results
        }

        report_file = "tests/artifacts/responsive_test_report.json"
        Path(report_file).parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"\\n💾 Detailed report saved: {report_file}")

        return failed_tests == 0


async def run_responsive_test_suite():
    """Run the complete responsive testing suite."""
    print("🚀 MultiCardz™ Responsive & Resizing Test Suite")
    print("=" * 60)
    print("Testing UI adaptation across all viewport sizes")
    print("=" * 60)

    tester = ResponsiveTestSuite(headless=False, slow_mo=50)

    try:
        await tester.setup()

        # Navigate to production app
        if not await tester.navigate_to_production_app():
            print("❌ Could not load production app")
            print("   Make sure the server is running: uv run python tests/integration/test_server.py")
            return False

        # Run test suites
        await tester.test_viewport_resize_sequence()
        await tester.test_card_display_maximization()
        await tester.test_dynamic_resizing_behavior()

        # Take screenshots
        await tester.take_responsive_screenshots()

        # Generate report
        success = tester.generate_responsive_report()

        if success:
            print("\\n🎉 All responsive tests passed!")
        else:
            print("\\n⚠️  Some responsive tests failed - check report for details")

        # Keep browser open for inspection
        print("\\n🔍 Browser will stay open for 10 seconds for inspection...")
        await asyncio.sleep(10)

        return success

    except Exception as e:
        print(f"❌ Responsive test suite failed: {e}")
        return False

    finally:
        await tester.teardown()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "headless":
        print("🤖 Running in HEADLESS mode")
        async def run_headless():
            tester = ResponsiveTestSuite(headless=True, slow_mo=20)
            await tester.setup()
            success = await run_responsive_test_suite()
            await tester.teardown()
            return success
        success = asyncio.run(run_headless())
    else:
        print("👁️  Running in VISUAL mode")
        success = asyncio.run(run_responsive_test_suite())

    sys.exit(0 if success else 1)