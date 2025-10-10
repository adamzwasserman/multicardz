#!/usr/bin/env python3
"""
Spatial Rendering Test for MultiCardz™
Tests the polymorphic spatial rendering system with real browser interactions.

Test Sequence:
1. Tag union1 in SHOW (union) zone → shows 2 cards
2. Add tag intersection1 in FILTER (intersection) zone → shows 1 card
3. Move tag union1 to EXCLUSION zone → shows 0 cards
4. Add tag union2 to SHOW (union) zone → shows 3 cards
5. Add tag column1 to column zone → creates 2D grid
6. Add tag row1 to row zone → creates 2D grid with rows/columns
"""

import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright, Page

# Test database path
TEST_DB_PATH = "/tmp/test_multicardz.db"
SERVER_URL = "http://localhost:8011"


class SpatialRenderingTest:
    """Test spatial rendering with real browser interactions."""

    def __init__(self, headless=False, slow_mo=500):
        self.headless = headless
        self.slow_mo = slow_mo
        self.browser = None
        self.page = None

    async def setup(self):
        """Setup browser and page."""
        print("🎬 Setting up Playwright browser...")

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )

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

    async def navigate_and_set_db(self):
        """Navigate to app (using default database with test data)."""
        print(f"\n🌐 Navigating to {SERVER_URL}...")

        await self.page.goto(SERVER_URL, wait_until="networkidle", timeout=10000)
        await asyncio.sleep(2)

        print("✅ Page loaded with test data")

    async def drag_tag_to_zone(self, tag_selector: str, zone_selector: str, description: str):
        """Drag a tag to a zone using real mouse interactions."""
        print(f"\n🖱️  {description}")

        # Find tag and zone
        tag = self.page.locator(tag_selector).first
        zone = self.page.locator(zone_selector).first

        # Get bounding boxes
        tag_box = await tag.bounding_box()
        zone_box = await zone.bounding_box()

        if not tag_box or not zone_box:
            raise Exception(f"Could not find tag or zone: {tag_selector} -> {zone_selector}")

        # Perform drag and drop
        await self.page.mouse.move(
            tag_box["x"] + tag_box["width"] / 2,
            tag_box["y"] + tag_box["height"] / 2
        )
        await self.page.mouse.down()
        await asyncio.sleep(0.3)
        await self.page.mouse.move(
            zone_box["x"] + zone_box["width"] / 2,
            zone_box["y"] + zone_box["height"] / 2,
            steps=10
        )
        await self.page.mouse.up()
        await asyncio.sleep(2)  # Wait for render and DOM updates

        print(f"  ✅ Drag complete")

    async def count_visible_cards(self) -> int:
        """Count visible cards in the display."""
        count = await self.page.locator(".card-item").count()
        return count

    async def verify_card_count(self, expected: int, description: str):
        """Verify the number of visible cards."""
        actual = await self.count_visible_cards()

        # Debug: Check tagsInPlay state
        tags_in_play = await self.page.evaluate("window.tagsInPlay")
        print(f"  🔍 tagsInPlay state: {tags_in_play}")

        if actual == expected:
            print(f"  ✅ {description}: {actual} cards (expected {expected})")
            return True
        else:
            print(f"  ❌ {description}: {actual} cards (expected {expected})")
            return False

    async def take_screenshot(self, filename: str):
        """Take screenshot for debugging."""
        filepath = Path(f"tests/artifacts/{filename}")
        await self.page.screenshot(path=str(filepath))
        print(f"📸 Screenshot saved: {filepath}")


async def run_spatial_test():
    """Run the complete spatial rendering test."""
    print("🚀 MultiCardz™ Spatial Rendering Test")
    print("=" * 60)

    tester = SpatialRenderingTest(headless=False, slow_mo=300)

    try:
        await tester.setup()
        await tester.navigate_and_set_db()

        # Test 1: Drag union1 to SHOW (union) zone
        print("\n" + "=" * 60)
        print("TEST 1: Drag union1 to SHOW (union) zone")
        print("Expected: 2 cards (card1 with [union1], card2 with [union1, intersection1])")
        print("=" * 60)

        await tester.drag_tag_to_zone(
            ".tag[data-tag='union1']",
            ".drop-zone.union-zone",
            "Drag union1 tag to SHOW zone"
        )

        success1 = await tester.verify_card_count(2, "After union1 in SHOW zone")
        await tester.take_screenshot("test1_union1_in_show.png")

        # Test 2: Add intersection1 to FILTER (intersection) zone
        print("\n" + "=" * 60)
        print("TEST 2: Add intersection1 to FILTER (intersection) zone")
        print("Expected: 1 card (card2 with [union1, intersection1])")
        print("=" * 60)

        await tester.drag_tag_to_zone(
            ".tag[data-tag='intersection1']",
            ".drop-zone.intersection-zone",
            "Drag intersection1 tag to FILTER zone"
        )

        success2 = await tester.verify_card_count(1, "After intersection1 in FILTER zone")
        await tester.take_screenshot("test2_intersection_filter.png")

        # Test 3: Move union1 to EXCLUSION zone
        print("\n" + "=" * 60)
        print("TEST 3: Move union1 from SHOW to EXCLUSION zone")
        print("Expected: 0 cards (excluding all cards with union1)")
        print("=" * 60)

        await tester.drag_tag_to_zone(
            ".union-zone .tag[data-tag='union1']",
            ".drop-zone.exclusion-zone",
            "Move union1 from SHOW to EXCLUSION zone"
        )

        success3 = await tester.verify_card_count(0, "After union1 in EXCLUSION zone")
        await tester.take_screenshot("test3_union1_exclusion.png")

        # Clear zones before test 4
        print("\n🧹 Clearing zones before test 4...")
        await tester.drag_tag_to_zone(
            ".intersection-zone .tag[data-tag='intersection1']",
            ".cloud-user .tags-wrapper",
            "Move intersection1 back to tag palette"
        )
        print("  ✅ intersection1 removed from FILTER zone")

        await tester.drag_tag_to_zone(
            ".exclusion-zone .tag[data-tag='union1']",
            ".cloud-user .tags-wrapper",
            "Move union1 back to tag palette"
        )
        print("  ✅ union1 removed from EXCLUSION zone")

        # Test 4: Add union2 to SHOW zone
        print("\n" + "=" * 60)
        print("TEST 4: Add union2 to SHOW (union) zone")
        print("Expected: 3 cards (card3, card4, card5 all with union2)")
        print("=" * 60)

        await tester.drag_tag_to_zone(
            ".tag[data-tag='union2']",
            ".drop-zone.union-zone",
            "Drag union2 tag to SHOW zone"
        )

        success4 = await tester.verify_card_count(3, "After union2 in SHOW zone")
        await tester.take_screenshot("test4_union2_in_show.png")

        # Test 5: Add column1 to column zone (1D grid)
        print("\n" + "=" * 60)
        print("TEST 5: Add column1 to column zone")
        print("Expected: 1D column grid with 3 unique cards, 8 total renderings (polymorphic)")
        print("=" * 60)

        await tester.drag_tag_to_zone(
            ".tag[data-tag='column1']",
            ".drop-zone.column-zone",
            "Drag column1 tag to column zone"
        )

        success5 = await tester.verify_card_count(8, "After column1 creates 1D grid")
        await tester.take_screenshot("test5_column_2d_grid.png")

        # Test 6: Add row1 to row zone (complete 2D grid)
        print("\n" + "=" * 60)
        print("TEST 6: Add row1 to row zone")
        print("Expected: 2D grid with 3 unique cards, 10 total renderings (polymorphic)")
        print("=" * 60)

        await tester.drag_tag_to_zone(
            ".tag[data-tag='row1']",
            ".drop-zone.row-zone",
            "Drag row1 tag to row zone"
        )

        success6 = await tester.verify_card_count(10, "After row1 completes 2D grid")
        await tester.take_screenshot("test6_row_column_2d_grid.png")

        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        all_tests = [success1, success2, success3, success4, success5, success6]
        passed = sum(all_tests)
        total = len(all_tests)

        print(f"Passed: {passed}/{total}")

        for i, success in enumerate(all_tests, 1):
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  Test {i}: {status}")

        if all(all_tests):
            print("\n🎉 All spatial rendering tests PASSED!")
            return True
        else:
            print("\n⚠️  Some tests FAILED!")
            return False

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        await tester.take_screenshot("error_state.png")
        return False

    finally:
        print("\n🔍 Browser will stay open for 10 seconds for inspection...")
        await asyncio.sleep(10)
        await tester.teardown()


if __name__ == "__main__":
    success = asyncio.run(run_spatial_test())
    sys.exit(0 if success else 1)
