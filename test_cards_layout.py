#!/usr/bin/env python3
"""Test card layout with Playwright."""

from playwright.sync_api import sync_playwright
import time

def test_cards():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_viewport_size({"width": 1200, "height": 800})

        print("🔍 Loading page...")
        page.goto("http://127.0.0.1:8011/?lesson=1")
        page.wait_for_load_state("networkidle")

        print("\n📸 Taking before screenshot...")
        page.screenshot(path="/tmp/before_drag.png", full_page=True)

        # Drag blue tag to SHOW zone
        print("\n🎯 Dragging blue tag to SHOW zone...")
        blue_tag = page.locator('.tag[data-tag="drag me to the SHOW box"]')
        show_zone = page.locator('[data-zone-type="union"] .tag-collection').first

        blue_tag.drag_to(show_zone)
        time.sleep(2)

        print("\n📸 Taking after screenshot...")
        page.screenshot(path="/tmp/after_drag.png", full_page=True)

        # Check cards
        cards = page.locator('.card-item').all()
        print(f"\n📇 Cards visible: {len(cards)}")

        if len(cards) > 0:
            # Get card positions
            for i, card in enumerate(cards[:5]):
                box = card.bounding_box()
                title = card.locator('.card-title').inner_text()
                print(f"   Card {i+1}: '{title}'")
                print(f"           Position: x={box['x']:.0f}, y={box['y']:.0f}, w={box['width']:.0f}, h={box['height']:.0f}")

            # Check if cards are wrapping (same row or different rows)
            if len(cards) >= 2:
                box1 = cards[0].bounding_box()
                box2 = cards[1].bounding_box()

                y_diff = abs(box1['y'] - box2['y'])
                if y_diff < 10:
                    print(f"\n✅ Cards on SAME row (y diff: {y_diff:.0f}px)")
                else:
                    print(f"\n⚠️  Cards on DIFFERENT rows (y diff: {y_diff:.0f}px)")

            # Check card-display container
            card_display = page.locator('.card-display').first
            if card_display.count() > 0:
                display_box = card_display.bounding_box()
                styles = card_display.evaluate('''el => {
                    const style = getComputedStyle(el);
                    return {
                        display: style.display,
                        flexDirection: style.flexDirection,
                        flexWrap: style.flexWrap,
                        width: style.width
                    }
                }''')
                print(f"\n📦 .card-display styles:")
                print(f"   display: {styles['display']}")
                print(f"   flex-direction: {styles['flexDirection']}")
                print(f"   flex-wrap: {styles['flexWrap']}")
                print(f"   width: {styles['width']}")

            # Check card-container
            card_container = page.locator('.card-container').first
            if card_container.count() > 0:
                styles = card_container.evaluate('''el => {
                    const style = getComputedStyle(el);
                    return {
                        display: style.display,
                        flexWrap: style.flexWrap,
                        width: style.width
                    }
                }''')
                print(f"\n📦 .card-container styles:")
                print(f"   display: {styles['display']}")
                print(f"   flex-wrap: {styles['flexWrap']}")
                print(f"   width: {styles['width']}")

        print("\n💾 Screenshots saved:")
        print("   /tmp/before_drag.png")
        print("   /tmp/after_drag.png")

        print("\n⏸️  Keeping browser open for 15 seconds...")
        time.sleep(15)

        browser.close()

if __name__ == "__main__":
    test_cards()
