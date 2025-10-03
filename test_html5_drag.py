#!/usr/bin/env python3
"""Test with HTML5 drag events (drag_to method)."""

from playwright.sync_api import sync_playwright
import time

def test_html5_drag():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        page = browser.new_page()
        page.set_viewport_size({"width": 1200, "height": 800})

        print("🔍 Loading page...")
        page.goto("http://127.0.0.1:8011/?lesson=1", wait_until="networkidle")
        time.sleep(1)

        # Check dimensions
        tag_collection = page.locator('[data-zone-type="union"] .tag-collection').first
        box = tag_collection.bounding_box()
        print(f"Tag collection: x={box['x']:.0f}, y={box['y']:.0f}, w={box['width']:.0f}, h={box['height']:.0f}")

        # Use drag_to which triggers proper HTML5 events
        print("\n🎯 Dragging with HTML5 events...")
        blue_tag = page.locator('.tag[data-tag="drag me to the SHOW box"]')

        # Drag to the tag-collection specifically
        blue_tag.drag_to(tag_collection)
        time.sleep(3)

        print("✅ Drag completed\n")

        # Check results
        tags_in_zone = page.locator('[data-zone-type="union"] .tag').all()
        print(f"Tags in union zone: {len(tags_in_zone)}")
        for i, tag in enumerate(tags_in_zone):
            print(f"  Tag {i+1}: {tag.inner_text()}")

        cards = page.locator('.card-item').all()
        print(f"\n📇 Cards visible: {len(cards)}")

        if len(cards) >= 2:
            print("\nCard layout:")
            for i in range(min(3, len(cards))):
                box = cards[i].bounding_box()
                title = cards[i].locator('.card-title').inner_text()
                print(f"  Card {i+1}: '{title}'")
                print(f"           x={box['x']:.0f}, y={box['y']:.0f}, w={box['width']:.0f}, h={box['height']:.0f}")

            # Check wrapping
            box1 = cards[0].bounding_box()
            box2 = cards[1].bounding_box()
            y_diff = abs(box1['y'] - box2['y'])

            if y_diff < 10:
                print(f"\n✅ Cards on SAME row (horizontal layout with wrapping)")
            else:
                print(f"\n❌ Cards on DIFFERENT rows (vertical stacking)")
                print(f"   Y difference: {y_diff:.0f}px")

                # Debug: check container styles
                card_grid = page.locator('.card-grid').first
                if card_grid.count() > 0:
                    styles = card_grid.evaluate('''el => {
                        const style = getComputedStyle(el);
                        return {
                            display: style.display,
                            flexDirection: style.flexDirection,
                            flexWrap: style.flexWrap
                        }
                    }''')
                    print(f"\n   .card-grid styles: {styles}")

        print("\n⏸️  Browser stays open for 10s...")
        time.sleep(10)

        browser.close()

if __name__ == "__main__":
    test_html5_drag()
