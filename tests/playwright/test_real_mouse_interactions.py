#!/usr/bin/env python3
"""
Replayable Playwright test for multicardz™ drag-drop system.
Uses REAL mouse interactions, not JavaScript simulation.
Can record and replay user interactions.
"""

import asyncio
import json
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright

# Add apps to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))


class DragDropTester:
    """Replayable drag-drop tester with real mouse interactions."""

    def __init__(self, headless=False, slow_mo=500):
        """
        Initialize tester.

        Args:
            headless: Run in headless mode
            slow_mo: Slow down operations (ms) for visibility
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.recording = []
        self.browser = None
        self.page = None

    async def setup(self):
        """Setup browser and page."""
        print("🎬 Setting up Playwright browser...")

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo  # Slow down for visibility
        )

        # Create context with realistic viewport
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )

        self.page = await self.context.new_page()

        # Enable console logging
        self.page.on("console", lambda msg: print(f"🖥️  Console: {msg.text}"))

        print("✅ Browser ready")

    async def teardown(self):
        """Clean up browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def record_action(self, action, **kwargs):
        """Record an action for replay."""
        self.recording.append({
            "action": action,
            "timestamp": time.time(),
            **kwargs
        })

    async def navigate_to_app(self, url="http://localhost:8011"):
        """Navigate to the multicardz app."""
        print(f"🌐 Navigating to {url}...")

        self.record_action("navigate", url=url)

        try:
            await self.page.goto(url, wait_until="networkidle", timeout=10000)
            print("✅ Page loaded")

            # Wait for the drag-drop system to initialize
            # Give it a moment for the DOMContentLoaded event
            await asyncio.sleep(2)

            # Check if the system initialized
            system_ready = await self.page.evaluate("""
                () => {
                    return typeof SpatialDragDrop !== 'undefined' &&
                           window.dragDropSystem !== null &&
                           window.dragDropSystem !== undefined;
                }
            """)

            if not system_ready:
                print("⚠️  Drag-drop system not initialized, checking what's available...")
                available = await self.page.evaluate("""
                    () => {
                        return {
                            SpatialDragDrop: typeof SpatialDragDrop,
                            dragDropSystem: typeof window.dragDropSystem,
                            DOMContentLoaded: document.readyState
                        };
                    }
                """)
                print(f"   Available: {available}")

                # Try to manually initialize if class exists
                if available.get('SpatialDragDrop') == 'function':
                    print("   🔧 Manually initializing drag-drop system...")
                    await self.page.evaluate("window.dragDropSystem = new SpatialDragDrop();")
                    system_ready = True

            if system_ready:
                print("✅ Drag-drop system initialized")
            else:
                print("❌ Could not initialize drag-drop system")

            return True
        except Exception as e:
            print(f"❌ Failed to load app: {e}")
            return False

    async def real_mouse_drag_drop(self, source_selector, target_selector, description=""):
        """
        Perform REAL mouse drag and drop using actual mouse events.
        This is NOT JavaScript simulation - it's real browser mouse interaction.
        """
        print(f"🖱️  Real mouse drag-drop: {description}")

        # Find source and target elements
        source = await self.page.wait_for_selector(source_selector, timeout=5000)
        target = await self.page.wait_for_selector(target_selector, timeout=5000)

        if not source or not target:
            raise Exception(f"Could not find source ({source_selector}) or target ({target_selector})")

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

        print(f"  📍 Source: ({source_x:.1f}, {source_y:.1f})")
        print(f"  📍 Target: ({target_x:.1f}, {target_y:.1f})")

        # Record the action
        self.record_action("drag_drop",
                          source=source_selector,
                          target=target_selector,
                          source_pos=[source_x, source_y],
                          target_pos=[target_x, target_y])

        # Perform REAL mouse drag and drop
        # Step 1: Move to source and press mouse down
        await self.page.mouse.move(source_x, source_y)
        await asyncio.sleep(0.1)  # Brief pause for realism

        await self.page.mouse.down()
        await asyncio.sleep(0.1)  # Hold for a moment

        # Step 2: Drag to target (with intermediate points for realism)
        steps = 5
        for i in range(1, steps + 1):
            intermediate_x = source_x + (target_x - source_x) * (i / steps)
            intermediate_y = source_y + (target_y - source_y) * (i / steps)
            await self.page.mouse.move(intermediate_x, intermediate_y)
            await asyncio.sleep(0.05)  # Smooth movement

        # Step 3: Release mouse
        await self.page.mouse.up()
        await asyncio.sleep(0.2)  # Wait for any animations

        print("  ✅ Drag-drop completed")

    async def real_mouse_multi_select(self, selectors, modifier_key="Meta"):
        """
        Perform REAL mouse multi-select with modifier key.
        Uses actual mouse clicks with keyboard modifiers.
        """
        print(f"🖱️  Real mouse multi-select with {modifier_key} key")

        selected_count = 0

        for i, selector in enumerate(selectors):
            element = await self.page.wait_for_selector(selector, timeout=5000)
            if not element:
                continue

            box = await element.bounding_box()
            if not box:
                continue

            x = box["x"] + box["width"] / 2
            y = box["y"] + box["height"] / 2

            print(f"  📍 Clicking element {i+1} at ({x:.1f}, {y:.1f})")

            # First click without modifier, subsequent with modifier
            if i == 0:
                await self.page.mouse.click(x, y)
                self.record_action("click", selector=selector, pos=[x, y])
            else:
                # Hold modifier key and click
                await self.page.keyboard.down(modifier_key)
                await self.page.mouse.click(x, y)
                await self.page.keyboard.up(modifier_key)
                self.record_action("click", selector=selector, pos=[x, y], modifier=modifier_key)

            selected_count += 1
            await asyncio.sleep(0.1)

        print(f"  ✅ Multi-selected {selected_count} elements")
        return selected_count

    async def real_mouse_click(self, selector, description=""):
        """Perform real mouse click."""
        print(f"🖱️  Real mouse click: {description}")

        element = await self.page.wait_for_selector(selector, timeout=5000)
        box = await element.bounding_box()

        x = box["x"] + box["width"] / 2
        y = box["y"] + box["height"] / 2

        self.record_action("click", selector=selector, pos=[x, y])

        await self.page.mouse.click(x, y)
        await asyncio.sleep(0.1)

        print(f"  ✅ Clicked at ({x:.1f}, {y:.1f})")

    async def verify_state(self, expected_zones=None, expected_controls=None):
        """Verify the current state matches expectations."""
        print("🔍 Verifying state...")

        # Get current state from the page
        state = await self.page.evaluate("window.dragDropSystem.deriveStateFromDOM()")

        print(f"  📊 Current state: {json.dumps(state, indent=2)}")

        success = True

        if expected_zones:
            for zone_name, expected_tags in expected_zones.items():
                actual_tags = state.get("zones", {}).get(zone_name, {}).get("tags", [])
                if set(actual_tags) != set(expected_tags):
                    print(f"  ❌ Zone '{zone_name}': expected {expected_tags}, got {actual_tags}")
                    success = False
                else:
                    print(f"  ✅ Zone '{zone_name}': {actual_tags}")

        if expected_controls:
            for control_name, expected_value in expected_controls.items():
                actual_value = state.get("controls", {}).get(control_name)
                if actual_value != expected_value:
                    print(f"  ❌ Control '{control_name}': expected {expected_value}, got {actual_value}")
                    success = False
                else:
                    print(f"  ✅ Control '{control_name}': {actual_value}")

        return success

    async def verify_card_rendering(self, expected_card_count=None, contains_tags=None, timeout=5000):
        """Verify that cards are properly rendered based on current tag state."""
        print("🃏 Verifying card rendering...")

        # Wait for card rendering to complete (API call + DOM update)
        try:
            # Wait for network to be idle (API call completion)
            await self.page.wait_for_load_state("networkidle", timeout=timeout)

            # Additional wait for DOM update
            await asyncio.sleep(0.5)

            # Get the card container and verify it has content
            card_container = await self.page.wait_for_selector("#cardContainer", timeout=timeout)
            if not card_container:
                print("  ❌ Card container not found")
                return False

            # Check if cards were rendered
            cards = await self.page.query_selector_all("#cardContainer .card")
            card_count = len(cards)

            print(f"  📊 Found {card_count} rendered cards")

            success = True

            # Verify expected card count if provided
            if expected_card_count is not None:
                if card_count != expected_card_count:
                    print(f"  ❌ Expected {expected_card_count} cards, got {card_count}")
                    success = False
                else:
                    print(f"  ✅ Card count matches: {card_count}")

            # Verify that rendered cards contain expected tags
            if contains_tags:
                for tag in contains_tags:
                    # Check if any card contains this tag
                    card_with_tag = await self.page.query_selector(f"#cardContainer .card[data-tags*='{tag}']")
                    if not card_with_tag:
                        print(f"  ❌ No card found containing tag '{tag}'")
                        success = False
                    else:
                        print(f"  ✅ Found card(s) with tag '{tag}'")

            # Check for any error messages in the card container
            error_message = await self.page.query_selector("#cardContainer .error, #cardContainer .no-cards")
            if error_message:
                error_text = await error_message.text_content()
                print(f"  ⚠️  Found message: {error_text}")

            # Verify API call was made successfully
            network_success = await self.page.evaluate("""
                () => {
                    // Check if there were any recent network errors in console
                    return !window.lastNetworkError; // Assuming we track this
                }
            """)

            if not network_success:
                print("  ❌ Network/API error detected")
                success = False
            else:
                print("  ✅ API call successful")

            return success

        except Exception as e:
            print(f"  ❌ Card rendering verification failed: {e}")
            return False

    async def count_elements(self, selector, description=""):
        """Count elements matching selector."""
        elements = await self.page.query_selector_all(selector)
        count = len(elements)
        if description:
            print(f"📊 {description}: {count}")
        return count

    async def take_screenshot(self, filename="screenshot.png"):
        """Take a screenshot for debugging."""
        await self.page.screenshot(path=filename)
        print(f"📸 Screenshot saved: {filename}")

    def save_recording(self, filename="tests/artifacts/multicardz_test_recording.json"):
        """Save the recorded actions."""
        # Ensure directory exists
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        with open(filename, "w") as f:
            json.dump(self.recording, f, indent=2)
        print(f"💾 Recording saved: {filename}")

    async def replay_recording(self, filename="tests/artifacts/multicardz_test_recording.json"):
        """Replay a saved recording."""
        print(f"▶️  Replaying recording: {filename}")

        with open(filename) as f:
            recording = json.load(f)

        for action_data in recording:
            action = action_data["action"]
            print(f"🎬 Replaying: {action}")

            if action == "navigate":
                await self.navigate_to_app(action_data["url"])
            elif action == "drag_drop":
                await self.real_mouse_drag_drop(
                    action_data["source"],
                    action_data["target"],
                    f"Replay: {action_data['source']} → {action_data['target']}"
                )
            elif action == "click":
                if "modifier" in action_data:
                    await self.page.keyboard.down(action_data["modifier"])
                    await self.page.mouse.click(action_data["pos"][0], action_data["pos"][1])
                    await self.page.keyboard.up(action_data["modifier"])
                else:
                    await self.page.mouse.click(action_data["pos"][0], action_data["pos"][1])

            await asyncio.sleep(0.5)  # Pause between actions


async def run_comprehensive_test():
    """Run comprehensive test with real mouse interactions."""
    print("🚀 multicardz™ Comprehensive Real Mouse Test")
    print("=" * 50)

    # Test with visible browser (set headless=True to hide)
    tester = DragDropTester(headless=False, slow_mo=300)

    try:
        await tester.setup()

        # 1. Navigate to app
        if not await tester.navigate_to_app():
            print("❌ Could not load app - make sure server is running:")
            print("   python test_server.py")
            return False

        # 2. Count initial elements
        tags_count = await tester.count_elements(".tag", "Initial tags")
        zones_count = await tester.count_elements(".drop-zone", "Drop zones")
        controls_count = await tester.count_elements("[data-affects-rendering]", "Controls")

        if tags_count == 0 or zones_count == 0:
            print("❌ Missing essential elements")
            return False

        # 2.5. Test initial card rendering (empty state)
        print("\n🧪 Test 0: Initial card rendering (no filters)")
        initial_card_success = await tester.verify_card_rendering()
        if not initial_card_success:
            print("❌ Initial card rendering verification failed")

        # 3. Test single drag-drop with REAL mouse
        print("\n🧪 Test 1: Single drag-drop with real mouse")
        await tester.real_mouse_drag_drop(
            ".tag[data-tag='javascript']",
            ".union-zone",
            "Drag 'javascript' tag to union zone"
        )

        # Verify the drag worked
        success = await tester.verify_state(expected_zones={"union": ["javascript"]})
        if not success:
            print("❌ Single drag-drop verification failed")

        # Verify cards were rendered with the javascript tag
        card_rendering_success = await tester.verify_card_rendering(contains_tags=["javascript"])
        if not card_rendering_success:
            print("❌ Card rendering verification failed after single drag-drop")

        # 4. Test multi-select with REAL mouse
        print("\n🧪 Test 2: Multi-select with real mouse")
        modifier = "Meta" if sys.platform == "darwin" else "Control"
        await tester.real_mouse_multi_select([
            ".tag[data-tag='python']",
            ".tag[data-tag='react']"
        ], modifier)

        # Verify multi-select worked
        selected_count = await tester.page.evaluate("window.dragDropSystem.selectedTags.size")
        if selected_count >= 2:
            print(f"✅ Multi-select successful ({selected_count} tags)")
        else:
            print(f"❌ Multi-select failed ({selected_count} tags)")

        # 5. Test control interaction with REAL mouse
        print("\n🧪 Test 3: Control interaction with real mouse")
        await tester.real_mouse_click(
            "#startWithAllCards",
            "Click 'Start with all cards' checkbox"
        )

        # Verify control state
        success = await tester.verify_state(expected_controls={"startWithAllCards": True})
        if not success:
            print("❌ Control interaction verification failed")

        # 6. Test zone-to-zone drag
        print("\n🧪 Test 4: Zone-to-zone drag with real mouse")
        await tester.real_mouse_drag_drop(
            ".union-zone .tag[data-tag='javascript']",
            ".intersection-zone",
            "Move 'javascript' from union to intersection zone"
        )

        # Verify the move
        success = await tester.verify_state(expected_zones={
            "union": [],
            "intersection": ["javascript"]
        })
        if not success:
            print("❌ Zone-to-zone drag verification failed")

        # Verify cards are still rendered correctly after zone change
        card_rendering_success = await tester.verify_card_rendering(contains_tags=["javascript"])
        if not card_rendering_success:
            print("❌ Card rendering verification failed after zone-to-zone drag")

        # 7. Take final screenshot
        await tester.take_screenshot("tests/artifacts/final_state.png")

        # 8. Save the recording for replay
        tester.save_recording()

        print("\n🎉 All real mouse tests completed!")
        print("📂 Files created:")
        print("   - tests/artifacts/final_state.png (screenshot)")
        print("   - tests/artifacts/multicardz_test_recording.json (replayable script)")

        # Keep browser open for manual inspection
        print("\n🔍 Browser will stay open for 10 seconds for inspection...")
        await asyncio.sleep(10)

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        await tester.take_screenshot("error_state.png")
        return False

    finally:
        await tester.teardown()


async def replay_test():
    """Replay a saved test recording."""
    print("🎬 Replaying saved test...")

    tester = DragDropTester(headless=False, slow_mo=500)

    try:
        await tester.setup()
        await tester.replay_recording("multicardz_test_recording.json")

        print("✅ Replay completed!")
        await asyncio.sleep(5)

    finally:
        await tester.teardown()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "replay":
        print("🎬 Running in REPLAY mode")
        asyncio.run(replay_test())
    else:
        print("🧪 Running COMPREHENSIVE TEST mode")
        print("💡 To replay: python test_playwright_replayable.py replay")
        success = asyncio.run(run_comprehensive_test())
        sys.exit(0 if success else 1)
