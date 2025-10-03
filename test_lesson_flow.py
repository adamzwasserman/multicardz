#!/usr/bin/env python3
"""Quick Playwright test to verify lesson flow and card display."""

from playwright.sync_api import sync_playwright
import time

def test_lesson_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()

        # Navigate to lesson 1
        print("🔍 Navigating to lesson 1...")
        page.goto("http://127.0.0.1:8011/?lesson=1")
        time.sleep(2)

        # Take screenshot of initial state
        page.screenshot(path="/tmp/lesson1_initial.png")
        print("📸 Screenshot: /tmp/lesson1_initial.png")

        # Check how many tags are visible
        tags = page.locator('.tag[data-tag]').all()
        print(f"✅ Found {len(tags)} tags")

        # Find the blue tag
        blue_tag = page.locator('.tag[data-tag="drag me to the SHOW box"]')
        if blue_tag.count() > 0:
            print(f"✅ Found blue tag: {blue_tag.inner_text()}")
            print(f"   Color: {blue_tag.evaluate('el => getComputedStyle(el).backgroundColor')}")

        # Check initial card count
        cards = page.locator('.card-item').all()
        print(f"📇 Initial cards visible: {len(cards)}")

        # Drag the blue tag to SHOW zone
        print("\n🎯 Dragging 'drag me to the SHOW box' to SHOW zone...")
        show_zone = page.locator('[data-zone-type="union"]').first
        blue_tag.drag_to(show_zone)
        time.sleep(2)

        # Take screenshot after drag
        page.screenshot(path="/tmp/lesson1_after_drag.png")
        print("📸 Screenshot: /tmp/lesson1_after_drag.png")

        # Check cards after drag
        cards_after = page.locator('.card-item').all()
        print(f"📇 Cards after drag: {len(cards_after)}")

        if len(cards_after) >= 2:
            print("✅ SUCCESS: 2 or more cards appeared!")
            for i, card in enumerate(cards_after[:3]):
                title = card.locator('.card-title').inner_text()
                tags_count = card.locator('.card-tag').count()
                tags_visible = card.locator('.card-tags').is_visible()
                print(f"   Card {i+1}: '{title}' - {tags_count} tags, visible: {tags_visible}")

                # Check if tags are actually displayed
                if tags_visible:
                    card_tags = card.locator('.card-tag').all()
                    tag_texts = [t.inner_text() for t in card_tags]
                    print(f"          Tags: {tag_texts}")
                else:
                    print(f"          ⚠️  Tags section not visible!")
        else:
            print(f"❌ FAIL: Expected 2 cards, got {len(cards_after)}")

        print("\n⏸️  Browser will stay open for 10 seconds for inspection...")
        time.sleep(10)

        browser.close()

if __name__ == "__main__":
    test_lesson_flow()
