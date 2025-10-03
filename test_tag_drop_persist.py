#!/usr/bin/env python3
"""Test tag drop persistence."""

from playwright.sync_api import sync_playwright
import time

def test_tag_drop():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        page = browser.new_page()
        page.set_viewport_size({"width": 1400, "height": 900})

        print("🔍 Loading page...")
        page.goto("http://127.0.0.1:8011/?lesson=1", wait_until="networkidle")
        time.sleep(1)

        # First create a tag
        print("\n📝 Creating tag 'test-tag'...")
        tag_input = page.locator('.cloud-user .tag-input').first
        tag_input.fill('test-tag')
        tag_input.press('Enter')
        time.sleep(1)

        # Drag blue tag to SHOW to reveal cards
        print("\n🎯 Dragging 'drag me to the SHOW box' to SHOW...")
        blue_tag = page.locator('.tag[data-tag="drag me to the SHOW box"]')
        show_zone = page.locator('[data-zone-type="union"] .tag-collection').first
        blue_tag.drag_to(show_zone)
        time.sleep(2)

        cards = page.locator('.card-item').all()
        print(f"\n📇 Cards visible: {len(cards)}")

        if len(cards) > 0:
            first_card = cards[0]
            card_id = first_card.get_attribute('data-card-id')
            print(f"First card ID: {card_id}")

            # Check initial tags
            initial_tags = first_card.locator('.card-tag').all()
            print(f"Initial tags on card: {[t.inner_text().replace(' ×', '') for t in initial_tags]}")

            # Drag test-tag from cloud to the card's tag area
            print("\n🎯 Dragging 'test-tag' to first card...")
            test_tag = page.locator('.tag[data-tag="test-tag"]')
            card_tags_area = first_card.locator('.card-tags')

            test_tag.drag_to(card_tags_area)
            time.sleep(2)

            # Check tags after drop
            after_tags = first_card.locator('.card-tag').all()
            print(f"Tags after drop: {[t.inner_text().replace(' ×', '') for t in after_tags]}")

            # Reload page
            print("\n🔄 Reloading page...")
            page.reload(wait_until="networkidle")
            time.sleep(2)

            # Drag blue tag again to show cards
            blue_tag2 = page.locator('.tag[data-tag="drag me to the SHOW box"]')
            show_zone2 = page.locator('[data-zone-type="union"] .tag-collection').first
            blue_tag2.drag_to(show_zone2)
            time.sleep(2)

            # Check if tag persisted
            cards_after_reload = page.locator('.card-item').all()
            if len(cards_after_reload) > 0:
                first_card_reload = cards_after_reload[0]
                reloaded_tags = first_card_reload.locator('.card-tag').all()
                reloaded_tag_texts = [t.inner_text().replace(' ×', '') for t in reloaded_tags]
                print(f"Tags after reload: {reloaded_tag_texts}")

                if 'test-tag' in reloaded_tag_texts:
                    print("\n✅ SUCCESS: Tag persisted!")
                else:
                    print("\n❌ FAIL: Tag did not persist after reload")

        print("\n⏸️  Browser open for 10s...")
        time.sleep(10)
        browser.close()

if __name__ == "__main__":
    test_tag_drop()
