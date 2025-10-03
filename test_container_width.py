#!/usr/bin/env python3
"""Debug container widths to find the constraint."""

from playwright.sync_api import sync_playwright
import time

def test_container_widths():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        page = browser.new_page()
        page.set_viewport_size({"width": 1200, "height": 800})

        page.goto("http://127.0.0.1:8011/?lesson=1", wait_until="networkidle")
        time.sleep(1)

        # Drag to show cards
        blue_tag = page.locator('.tag[data-tag="drag me to the SHOW box"]')
        tag_collection = page.locator('[data-zone-type="union"] .tag-collection').first
        blue_tag.drag_to(tag_collection)
        time.sleep(2)

        # Check all container widths
        print("📏 Container widths:\n")

        containers = [
            '.card-display-container',
            '.card-display',
            '.card-container',
            '.card-grid'
        ]

        for selector in containers:
            elem = page.locator(selector).first
            if elem.count() > 0:
                box = elem.bounding_box()
                styles = elem.evaluate('''el => {
                    const style = getComputedStyle(el);
                    return {
                        width: style.width,
                        maxWidth: style.maxWidth,
                        display: style.display,
                        flexDirection: style.flexDirection,
                        flexWrap: style.flexWrap
                    }
                }''')
                print(f"{selector}:")
                print(f"  Bounding box width: {box['width']:.0f}px")
                print(f"  Computed width: {styles['width']}")
                print(f"  Max-width: {styles['maxWidth']}")
                print(f"  Display: {styles['display']}, flex-direction: {styles['flexDirection']}, flex-wrap: {styles['flexWrap']}")
                print()

        # Check card widths
        cards = page.locator('.card-item').all()
        if len(cards) > 0:
            card_box = cards[0].bounding_box()
            print(f".card-item:")
            print(f"  Width: {card_box['width']:.0f}px")

        print("\n⏸️  Browser open for inspection...")
        time.sleep(15)

        browser.close()

if __name__ == "__main__":
    test_container_widths()
