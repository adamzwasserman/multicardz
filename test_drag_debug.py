#!/usr/bin/env python3
"""Debug drag operation to see what's happening."""

from playwright.sync_api import sync_playwright
import time

def test_drag_debug():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()
        page.set_viewport_size({"width": 1200, "height": 800})

        print("🔍 Loading page...")
        page.goto("http://127.0.0.1:8011/?lesson=1", wait_until="networkidle")
        time.sleep(1)

        # Check initial state
        print("\n📋 Initial state:")
        union_zone = page.locator('[data-zone-type="union"]')
        tags_in_zone = union_zone.locator('.tag').all()
        print(f"  Tags in union zone: {len(tags_in_zone)}")

        # Get positions
        blue_tag = page.locator('.tag[data-tag="drag me to the SHOW box"]')
        tag_collection = page.locator('[data-zone-type="union"] .tag-collection').first

        tag_box = blue_tag.bounding_box()
        collection_box = tag_collection.bounding_box()

        print(f"\n📍 Positions:")
        print(f"  Tag: x={tag_box['x']:.0f}, y={tag_box['y']:.0f}, w={tag_box['width']:.0f}, h={tag_box['height']:.0f}")
        print(f"  Collection: x={collection_box['x']:.0f}, y={collection_box['y']:.0f}, w={collection_box['width']:.0f}, h={collection_box['height']:.0f}")

        # Perform real mouse drag to the tag-collection specifically
        print("\n🖱️  Dragging to tag-collection...")

        tag_x = tag_box['x'] + tag_box['width'] / 2
        tag_y = tag_box['y'] + tag_box['height'] / 2

        # Target the tag-collection div
        coll_x = collection_box['x'] + 50  # Move into the collection area
        coll_y = collection_box['y'] + collection_box['height'] / 2

        page.mouse.move(tag_x, tag_y)
        time.sleep(0.2)
        page.mouse.down()
        time.sleep(0.2)
        page.mouse.move(coll_x, coll_y, steps=30)
        time.sleep(0.2)
        page.mouse.up()
        time.sleep(2)

        print("✅ Drag completed\n")

        # Check state after drag
        print("📋 After drag:")
        tags_in_zone_after = union_zone.locator('.tag').all()
        print(f"  Tags in union zone: {len(tags_in_zone_after)}")

        for i, tag in enumerate(tags_in_zone_after):
            tag_text = tag.inner_text()
            print(f"    Tag {i+1}: {tag_text}")

        # Check if the render was triggered
        cards = page.locator('.card-item').all()
        print(f"\n📇 Cards visible: {len(cards)}")

        # Check JavaScript console for errors
        print("\n🐛 Checking for JS errors...")
        page.on("console", lambda msg: print(f"  Console: {msg.text}"))

        print("\n⏸️  Keeping browser open for inspection (15s)...")
        time.sleep(15)

        browser.close()

if __name__ == "__main__":
    test_drag_debug()
