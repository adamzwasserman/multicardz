#!/usr/bin/env python3
"""Quick Playwright test to verify lesson flow and card display."""

from playwright.sync_api import sync_playwright
import time

def test_lesson_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to lesson 1
        print("🔍 Navigating to lesson 1...")
        page.goto("http://127.0.0.1:8011/?lesson=1", wait_until="networkidle")
        time.sleep(1)

        # Check how many tags are visible
        tags = page.locator('.tag[data-tag]').all()
        print(f"✅ Found {len(tags)} tags")

        # Find the blue tag
        blue_tag = page.locator('.tag[data-tag="drag me to the SHOW box"]')
        if blue_tag.count() > 0:
            print(f"✅ Found blue tag: {blue_tag.inner_text()}")

        # Check initial card count
        cards = page.locator('.card-item').all()
        print(f"📇 Initial cards visible: {len(cards)}")

        # Drag the blue tag to SHOW zone
        print("\n🎯 Dragging 'drag me to the SHOW box' to SHOW zone...")
        show_zone = page.locator('[data-zone-type="union"]').first
        blue_tag.drag_to(show_zone)
        time.sleep(2)

        # Check cards after drag
        cards_after = page.locator('.card-item').all()
        print(f"📇 Cards after drag: {len(cards_after)}")

        if len(cards_after) >= 2:
            print("✅ SUCCESS: 2 or more cards appeared!")
            for i, card in enumerate(cards_after[:3]):
                title = card.locator('.card-title').inner_text()

                # Check if card-tags-section exists
                tags_section = card.locator('.card-tags-section')
                if tags_section.count() > 0:
                    # Check if tags are visible
                    tags_div = card.locator('.card-tags')
                    tags_visible = tags_div.is_visible()
                    tags_count = card.locator('.card-tag').count()
                    print(f"   Card {i+1}: '{title}' - {tags_count} tags, visible: {tags_visible}")

                    if tags_visible and tags_count > 0:
                        card_tags = card.locator('.card-tag').all()
                        tag_texts = [t.inner_text() for t in card_tags]
                        print(f"          Tags: {tag_texts}")
                    else:
                        print(f"          ⚠️  Tags exist but not visible!")

                        # Check display style
                        display = tags_div.evaluate('el => getComputedStyle(el).display')
                        print(f"          Display style: {display}")
                else:
                    print(f"   Card {i+1}: '{title}' - ⚠️ No tags section found!")
        else:
            print(f"❌ FAIL: Expected 2 cards, got {len(cards_after)}")

        browser.close()

if __name__ == "__main__":
    test_lesson_flow()
