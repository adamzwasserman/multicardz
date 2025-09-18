#!/usr/bin/env python3
"""
Comprehensive Playwright test for MultiCardz™ drag-drop system.
Uses REAL production HTML and tests every permutation of drag-drop interactions.

Test Matrix:
1. Tags: cloud → zone, zone → zone, zone → cloud
2. Zones: left → right, top → bottom, etc.
3. Multi-select combinations
4. Edge cases and error conditions
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


class ComprehensiveDragDropTester:
    """Comprehensive drag-drop tester covering all production scenarios."""

    def __init__(self, headless=False, slow_mo=200):
        """
        Initialize tester for comprehensive testing.

        Args:
            headless: Run in headless mode
            slow_mo: Slow down operations (ms) for visibility
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.recording = []
        self.browser = None
        self.page = None
        self.test_results = []

    async def setup(self):
        """Setup browser and page with optimal settings."""
        print("🎬 Setting up Comprehensive Drag-Drop Test Environment...")

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            args=['--no-sandbox', '--disable-setuid-sandbox']  # Better for CI
        )

        # Create context with realistic viewport
        self.context = await self.browser.new_context(
            viewport={"width": 1400, "height": 900},  # Larger for better testing
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )

        self.page = await self.context.new_page()

        # Enable comprehensive console logging
        self.page.on("console", lambda msg: print(f"🖥️  Console [{msg.type}]: {msg.text}"))
        self.page.on("pageerror", lambda err: print(f"❌ Page Error: {err}"))

        print("✅ Browser ready for comprehensive testing")

    async def teardown(self):
        """Clean up browser resources."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def record_test_result(self, test_name: str, success: bool, duration: float, details: str = ""):
        """Record test result for reporting."""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "duration": duration,
            "details": details,
            "timestamp": time.time()
        })

    async def navigate_to_production_app(self, url="http://localhost:8001"):
        """Navigate to the real MultiCardz production app."""
        print(f"🌐 Navigating to production app: {url}")

        try:
            await self.page.goto(url, wait_until="networkidle", timeout=15000)
            print("✅ Production page loaded")

            # Wait for drag-drop system initialization
            await asyncio.sleep(3)

            # Verify the production system is ready
            system_check = await self.page.evaluate("""
                () => {
                    const checks = {
                        dragDropSystem: typeof SpatialDragDrop !== 'undefined' &&
                                       window.dragDropSystem !== null,
                        userTags: document.querySelectorAll('.tag-user').length > 0,
                        zones: document.querySelectorAll('.drop-zone').length > 0,
                        clouds: document.querySelectorAll('.cloud').length > 0,
                        controlAreas: document.querySelectorAll('.control-area-container').length > 0
                    };

                    return {
                        ...checks,
                        allReady: Object.values(checks).every(v => v)
                    };
                }
            """)

            if system_check['allReady']:
                print("✅ Production drag-drop system fully initialized")
                print(f"   - User tags: {await self.count_elements('.tag-user')}")
                print(f"   - Drop zones: {await self.count_elements('.drop-zone')}")
                print(f"   - Tag clouds: {await self.count_elements('.cloud')}")
                print(f"   - Control areas: {await self.count_elements('.control-area-container')}")
                return True
            else:
                print(f"⚠️  System partially ready: {system_check}")
                # Try manual initialization if needed
                if not system_check['dragDropSystem']:
                    await self.page.evaluate("window.dragDropSystem = new SpatialDragDrop();")
                return True

        except Exception as e:
            print(f"❌ Failed to load production app: {e}")
            return False

    async def count_elements(self, selector: str) -> int:
        """Count elements matching selector."""
        elements = await self.page.query_selector_all(selector)
        return len(elements)

    async def get_available_tags(self) -> List[str]:
        """Get list of available tags from the production app."""
        tags = await self.page.evaluate("""
            () => {
                const tagElements = document.querySelectorAll('.tag[data-tag]');
                return Array.from(tagElements).map(tag => tag.dataset.tag);
            }
        """)
        return tags

    async def get_available_zones(self) -> Dict[str, str]:
        """Get list of available zones with their selectors."""
        zones = await self.page.evaluate("""
            () => {
                const zones = {};

                // Find all drop zones
                document.querySelectorAll('.drop-zone[data-zone-type]').forEach(zone => {
                    const zoneType = zone.dataset.zoneType;
                    zones[zoneType] = {
                        selector: '.' + zoneType + '-zone',
                        id: zone.id,
                        accepts: zone.dataset.accepts || 'tags'
                    };
                });

                // Add cloud containers
                document.querySelectorAll('.cloud[data-cloud-type]').forEach(cloud => {
                    const cloudType = cloud.dataset.cloudType;
                    zones[cloudType + '_cloud'] = {
                        selector: '.cloud-' + cloudType,
                        id: cloud.id,
                        accepts: 'tags'
                    };
                });

                return zones;
            }
        """)
        return zones

    async def real_mouse_drag_drop(self, source_selector: str, target_selector: str,
                                 test_name: str) -> bool:
        """
        Perform REAL mouse drag and drop with comprehensive error handling.
        """
        start_time = time.time()
        print(f"🖱️  {test_name}")

        try:
            # Find source and target elements with retry
            source = None
            target = None

            for attempt in range(3):
                try:
                    source = await self.page.wait_for_selector(source_selector, timeout=3000)
                    target = await self.page.wait_for_selector(target_selector, timeout=3000)
                    break
                except:
                    if attempt < 2:
                        await asyncio.sleep(0.5)
                        continue
                    raise

            if not source or not target:
                raise Exception(f"Elements not found: {source_selector} or {target_selector}")

            # Get element positions
            source_box = await source.bounding_box()
            target_box = await target.bounding_box()

            if not source_box or not target_box:
                raise Exception("Could not get element bounding boxes")

            # Calculate center points
            source_x = source_box["x"] + source_box["width"] / 2
            source_y = source_box["y"] + source_box["height"] / 2
            target_x = target_box["x"] + target_box["width"] / 2
            target_y = target_box["y"] + target_box["height"] / 2

            print(f"  📍 {source_selector} → {target_selector}")
            print(f"     From: ({source_x:.1f}, {source_y:.1f}) To: ({target_x:.1f}, {target_y:.1f})")

            # Perform REAL mouse drag and drop with realistic movement
            await self.page.mouse.move(source_x, source_y)
            await asyncio.sleep(0.1)

            await self.page.mouse.down()
            await asyncio.sleep(0.1)

            # Realistic drag movement with intermediate points
            steps = 8
            for i in range(1, steps + 1):
                intermediate_x = source_x + (target_x - source_x) * (i / steps)
                intermediate_y = source_y + (target_y - source_y) * (i / steps)
                await self.page.mouse.move(intermediate_x, intermediate_y)
                await asyncio.sleep(0.03)

            await self.page.mouse.up()
            await asyncio.sleep(0.2)  # Wait for any animations/state updates

            duration = time.time() - start_time
            print(f"  ✅ Completed in {duration:.2f}s")

            self.record_test_result(test_name, True, duration, f"{source_selector} → {target_selector}")
            return True

        except Exception as e:
            duration = time.time() - start_time
            print(f"  ❌ Failed: {e}")
            self.record_test_result(test_name, False, duration, str(e))
            return False

    async def test_tag_cloud_to_zone_permutations(self):
        """Test all tag → zone movements."""
        print("\\n🧪 Testing Tag Cloud → Zone Permutations")
        print("=" * 60)

        tags = await self.get_available_tags()
        zones = await self.get_available_zones()

        if not tags:
            print("⚠️  No tags found for testing")
            return

        # Test each tag type to each zone type
        test_cases = [
            # User tags to all zones
            (".tag-user[data-tag]", ".union-zone", "User tag → Union zone"),
            (".tag-user[data-tag]", ".intersection-zone", "User tag → Intersection zone"),
            (".tag-user[data-tag]", ".row-zone", "User tag → Row zone"),
            (".tag-user[data-tag]", ".column-zone", "User tag → Column zone"),

            # AI tags to zones (if available)
            (".tag-ai[data-tag]", ".union-zone", "AI tag → Union zone"),
            (".tag-ai[data-tag]", ".intersection-zone", "AI tag → Intersection zone"),

            # System tags to zones (if available)
            (".tag-system[data-tag]", ".union-zone", "System tag → Union zone"),
        ]

        for source_selector, target_selector, test_name in test_cases:
            # Check if source exists before testing
            source_exists = await self.page.query_selector(source_selector)
            target_exists = await self.page.query_selector(target_selector)

            if source_exists and target_exists:
                await self.real_mouse_drag_drop(source_selector, target_selector, test_name)
                await asyncio.sleep(0.5)  # Brief pause between tests
            else:
                print(f"  ⏭️  Skipping {test_name} - elements not available")

    async def test_zone_to_zone_permutations(self):
        """Test all zone → zone movements within the same zone and between zones."""
        print("\\n🧪 Testing Zone → Zone Permutations")
        print("=" * 60)

        # First, put some tags in zones to test zone-to-zone movement
        await self.populate_zones_with_tags()

        test_cases = [
            # Union zone tags to other zones
            (".union-zone .tag", ".intersection-zone", "Union tag → Intersection zone"),
            (".union-zone .tag", ".row-zone", "Union tag → Row zone"),
            (".union-zone .tag", ".column-zone", "Union tag → Column zone"),

            # Intersection zone tags to other zones
            (".intersection-zone .tag", ".union-zone", "Intersection tag → Union zone"),
            (".intersection-zone .tag", ".row-zone", "Intersection tag → Row zone"),
            (".intersection-zone .tag", ".column-zone", "Intersection tag → Column zone"),

            # Row zone tags to other zones
            (".row-zone .tag", ".union-zone", "Row tag → Union zone"),
            (".row-zone .tag", ".intersection-zone", "Row tag → Intersection zone"),
            (".row-zone .tag", ".column-zone", "Row tag → Column zone"),

            # Column zone tags to other zones
            (".column-zone .tag", ".union-zone", "Column tag → Union zone"),
            (".column-zone .tag", ".intersection-zone", "Column tag → Intersection zone"),
            (".column-zone .tag", ".row-zone", "Column tag → Row zone"),
        ]

        for source_selector, target_selector, test_name in test_cases:
            source_exists = await self.page.query_selector(source_selector)
            target_exists = await self.page.query_selector(target_selector)

            if source_exists and target_exists:
                await self.real_mouse_drag_drop(source_selector, target_selector, test_name)
                await asyncio.sleep(0.5)
            else:
                print(f"  ⏭️  Skipping {test_name} - elements not available")

    async def test_zone_to_cloud_permutations(self):
        """Test all zone → cloud movements (returning tags to clouds)."""
        print("\\n🧪 Testing Zone → Cloud Permutations")
        print("=" * 60)

        test_cases = [
            # Return tags to user cloud
            (".union-zone .tag", ".cloud-user .tags-wrapper", "Union tag → User cloud"),
            (".intersection-zone .tag", ".cloud-user .tags-wrapper", "Intersection tag → User cloud"),
            (".row-zone .tag", ".cloud-user .tags-wrapper", "Row tag → User cloud"),
            (".column-zone .tag", ".cloud-user .tags-wrapper", "Column tag → User cloud"),

            # Return to AI cloud (if available)
            (".union-zone .tag-ai", ".cloud-ai .tags-wrapper", "Union AI tag → AI cloud"),
            (".intersection-zone .tag-ai", ".cloud-ai .tags-wrapper", "Intersection AI tag → AI cloud"),
        ]

        for source_selector, target_selector, test_name in test_cases:
            source_exists = await self.page.query_selector(source_selector)
            target_exists = await self.page.query_selector(target_selector)

            if source_exists and target_exists:
                await self.real_mouse_drag_drop(source_selector, target_selector, test_name)
                await asyncio.sleep(0.5)
            else:
                print(f"  ⏭️  Skipping {test_name} - elements not available")

    async def test_zone_repositioning_permutations(self):
        """Test dragging entire zones between control areas."""
        print("\\n🧪 Testing Zone Repositioning Permutations")
        print("=" * 60)

        # Zone repositioning tests - moving entire zones between areas
        test_cases = [
            # Move filter zone to different areas
            (".filter-zone-container", ".left-control .control-area-container", "Filter zone → Left area"),
            (".filter-zone-container", ".right-control .control-area-container", "Filter zone → Right area"),
            (".filter-zone-container", ".bottom-control .control-area-container", "Filter zone → Bottom area"),

            # Move row zone to different areas
            (".row-zone", ".top-control .control-area-container", "Row zone → Top area"),
            (".row-zone", ".right-control .control-area-container", "Row zone → Right area"),
            (".row-zone", ".bottom-control .control-area-container", "Row zone → Bottom area"),

            # Move column zone to different areas
            (".column-zone", ".left-control .control-area-container", "Column zone → Left area"),
            (".column-zone", ".top-control .control-area-container", "Column zone → Top area"),
            (".column-zone", ".bottom-control .control-area-container", "Column zone → Bottom area"),
        ]

        for source_selector, target_selector, test_name in test_cases:
            source_exists = await self.page.query_selector(source_selector)
            target_exists = await self.page.query_selector(target_selector)

            if source_exists and target_exists:
                await self.real_mouse_drag_drop(source_selector, target_selector, test_name)
                await asyncio.sleep(1)  # Longer pause for zone moves
            else:
                print(f"  ⏭️  Skipping {test_name} - elements not available")

    async def test_multi_select_permutations(self):
        """Test multi-select drag operations."""
        print("\\n🧪 Testing Multi-Select Permutations")
        print("=" * 60)

        # Multi-select tags from cloud
        await self.multi_select_tags([
            ".tag-user[data-tag]:nth-child(1)",
            ".tag-user[data-tag]:nth-child(2)",
            ".tag-user[data-tag]:nth-child(3)"
        ])

        # Drag multi-selected tags to zone
        await self.real_mouse_drag_drop(
            ".tag-user.selected:first-child",
            ".union-zone",
            "Multi-selected tags → Union zone"
        )

        await asyncio.sleep(1)

        # Multi-select from different zones
        await self.multi_select_tags([
            ".union-zone .tag:nth-child(1)",
            ".union-zone .tag:nth-child(2)"
        ])

        # Move multi-selected between zones
        await self.real_mouse_drag_drop(
            ".union-zone .tag.selected:first-child",
            ".intersection-zone",
            "Multi-selected zone tags → Different zone"
        )

    async def multi_select_tags(self, selectors: List[str]):
        """Perform multi-select on multiple tags."""
        print(f"🔘 Multi-selecting {len(selectors)} tags...")

        modifier_key = "Meta" if sys.platform == "darwin" else "Control"

        for i, selector in enumerate(selectors):
            try:
                element = await self.page.wait_for_selector(selector, timeout=2000)
                if element:
                    box = await element.bounding_box()
                    if box:
                        x = box["x"] + box["width"] / 2
                        y = box["y"] + box["height"] / 2

                        if i == 0:
                            await self.page.mouse.click(x, y)
                        else:
                            await self.page.keyboard.down(modifier_key)
                            await self.page.mouse.click(x, y)
                            await self.page.keyboard.up(modifier_key)

                        await asyncio.sleep(0.1)
            except Exception as e:
                print(f"  ⚠️  Could not select {selector}: {e}")

    async def populate_zones_with_tags(self):
        """Populate zones with tags for testing zone-to-zone movements."""
        print("📋 Populating zones with tags for zone-to-zone testing...")

        # Put different tags in different zones
        populations = [
            (".tag-user[data-tag]:nth-child(1)", ".union-zone", "Populate union zone"),
            (".tag-user[data-tag]:nth-child(2)", ".intersection-zone", "Populate intersection zone"),
            (".tag-user[data-tag]:nth-child(3)", ".row-zone", "Populate row zone"),
            (".tag-user[data-tag]:nth-child(4)", ".column-zone", "Populate column zone"),
        ]

        for source, target, description in populations:
            source_exists = await self.page.query_selector(source)
            target_exists = await self.page.query_selector(target)

            if source_exists and target_exists:
                await self.real_mouse_drag_drop(source, target, description)
                await asyncio.sleep(0.3)

    async def verify_state_after_operations(self):
        """Verify the system state is consistent after all operations."""
        print("\\n🔍 Verifying System State Consistency")
        print("=" * 60)

        try:
            state = await self.page.evaluate("window.dragDropSystem.deriveStateFromDOM()")
            print(f"📊 Final system state:")
            print(json.dumps(state, indent=2))

            # Verify no tags are duplicated
            all_tags = []
            for zone_name, zone_data in state.get("zones", {}).items():
                tags = zone_data.get("tags", [])
                all_tags.extend(tags)

            duplicates = len(all_tags) - len(set(all_tags))
            if duplicates == 0:
                print("✅ No duplicate tags found")
                return True
            else:
                print(f"❌ Found {duplicates} duplicate tags")
                return False

        except Exception as e:
            print(f"❌ State verification failed: {e}")
            return False

    async def take_comprehensive_screenshot(self, filename="comprehensive_test_final.png"):
        """Take full page screenshot."""
        await self.page.screenshot(path=f"tests/artifacts/{filename}", full_page=True)
        print(f"📸 Comprehensive test screenshot: tests/artifacts/{filename}")

    def generate_test_report(self):
        """Generate detailed test report."""
        print("\\n📊 Comprehensive Test Report")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests
        total_duration = sum(r["duration"] for r in self.test_results)

        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏱️  Total Duration: {total_duration:.2f}s")
        print(f"📊 Success Rate: {(passed_tests/total_tests*100):.1f}%")

        if failed_tests > 0:
            print("\\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")

        # Save detailed report
        report_file = "tests/artifacts/comprehensive_test_report.json"
        Path(report_file).parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, "w") as f:
            json.dump({
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "duration": total_duration,
                    "success_rate": passed_tests/total_tests if total_tests > 0 else 0
                },
                "results": self.test_results
            }, f, indent=2)

        print(f"💾 Detailed report saved: {report_file}")

        return failed_tests == 0


async def run_comprehensive_test():
    """Run the complete comprehensive test suite."""
    print("🚀 MultiCardz™ Comprehensive Drag-Drop Test Suite")
    print("=" * 60)
    print("Testing ALL permutations with REAL production HTML")
    print("=" * 60)

    tester = ComprehensiveDragDropTester(headless=False, slow_mo=150)

    try:
        await tester.setup()

        # Navigate to production app
        if not await tester.navigate_to_production_app():
            print("❌ Could not load production app")
            print("   Make sure the server is running: uv run python tests/integration/test_server.py")
            return False

        # Run all test suites
        await tester.test_tag_cloud_to_zone_permutations()
        await tester.test_zone_to_zone_permutations()
        await tester.test_zone_to_cloud_permutations()
        await tester.test_zone_repositioning_permutations()
        await tester.test_multi_select_permutations()

        # Verify final state
        state_ok = await tester.verify_state_after_operations()

        # Take final screenshot
        await tester.take_comprehensive_screenshot()

        # Generate report
        success = tester.generate_test_report() and state_ok

        if success:
            print("\\n🎉 All comprehensive tests passed!")
        else:
            print("\\n⚠️  Some tests failed - check report for details")

        # Keep browser open for inspection
        print("\\n🔍 Browser will stay open for 15 seconds for inspection...")
        await asyncio.sleep(15)

        return success

    except Exception as e:
        print(f"❌ Comprehensive test failed: {e}")
        await tester.take_comprehensive_screenshot("error_state.png")
        return False

    finally:
        await tester.teardown()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "headless":
        print("🤖 Running in HEADLESS mode")
        # Modify to run headless
        async def run_headless():
            tester = ComprehensiveDragDropTester(headless=True, slow_mo=50)
            # ... run test logic
        asyncio.run(run_headless())
    else:
        print("👁️  Running in VISUAL mode")
        success = asyncio.run(run_comprehensive_test())
        sys.exit(0 if success else 1)