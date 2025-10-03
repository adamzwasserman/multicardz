#!/usr/bin/env python3
"""Test card layout with real mouse drag (not JavaScript simulation)."""

from playwright.sync_api import sync_playwright
import time

def test_real_drag():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()
        page.set_viewport_size({"width": 1200, "height": 800})

        print("🔍 Loading page...")
        page.goto("http://127.0.0.1:8011/?lesson=1", wait_until="networkidle")
        time.sleep(1)

        # Get positions for real mouse drag
        blue_tag = page.locator('.tag[data-tag="drag me to the SHOW box"]')
        union_zone = page.locator('[data-zone-type="union"]')

        tag_box = blue_tag.bounding_box()
        zone_box = union_zone.bounding_box()

        print(f"Tag position: {tag_box}")
        print(f"Zone position: {zone_box}")

        # Perform real mouse drag
        print("\n🖱️  Starting real mouse drag...")

        # Move to tag center
        tag_x = tag_box['x'] + tag_box['width'] / 2
        tag_y = tag_box['y'] + tag_box['height'] / 2
        page.mouse.move(tag_x, tag_y)
        time.sleep(0.3)

        # Mouse down
        page.mouse.down()
        time.sleep(0.3)

        # Move to zone center
        zone_x = zone_box['x'] + zone_box['width'] / 2
        zone_y = zone_box['y'] + zone_box['height'] / 2
        page.mouse.move(zone_x, zone_y, steps=20)
        time.sleep(0.3)

        # Mouse up
        page.mouse.up()
        time.sleep(2)

        print("✅ Drag completed\n")

        # Check cards
        cards = page.locator('.card-item').all()
        print(f"📇 Cards visible: {len(cards)}")

        if len(cards) >= 2:
            print("\nCard positions:")
            for i in range(min(3, len(cards))):
                box = cards[i].bounding_box()
                print(f"  Card {i+1}: x={box['x']:.0f}, y={box['y']:.0f}, w={box['width']:.0f}, h={box['height']:.0f}")

            # Check wrapping
            box1 = cards[0].bounding_box()
            box2 = cards[1].bounding_box()
            y_diff = abs(box1['y'] - box2['y'])
            x_diff = box2['x'] - (box1['x'] + box1['width'])

            print(f"\nLayout analysis:")
            print(f"  Y difference: {y_diff:.0f}px")
            print(f"  X gap: {x_diff:.0f}px")

            if y_diff < 10:
                print(f"\n✅ Cards on SAME row (wrapping horizontally)")
            else:
                print(f"\n❌ Cards on DIFFERENT rows (stacking vertically)")

            # Check parent container styles
            card_container = page.locator('.card-container').first
            if card_container.count() > 0:
                styles = card_container.evaluate('''el => {
                    const style = getComputedStyle(el);
                    return {
                        display: style.display,
                        flexDirection: style.flexDirection,
                        flexWrap: style.flexWrap,
                        width: style.width
                    }
                }''')
                print(f"\n📦 .card-container computed styles:")
                for key, value in styles.items():
                    print(f"  {key}: {value}")

            # Check card-grid styles
            card_grid = page.locator('.card-grid').first
            if card_grid.count() > 0:
                styles = card_grid.evaluate('''el => {
                    const style = getComputedStyle(el);
                    return {
                        display: style.display,
                        flexDirection: style.flexDirection,
                        flexWrap: style.flexWrap,
                        width: style.width
                    }
                }''')
                print(f"\n📦 .card-grid computed styles:")
                for key, value in styles.items():
                    print(f"  {key}: {value}")

        print("\n⏸️  Keeping browser open for inspection...")
        time.sleep(10)

        browser.close()

if __name__ == "__main__":
    test_real_drag()
