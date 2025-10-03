#!/usr/bin/env python3
"""Test lesson 2 - drag 'drag me next' to SHOW box."""

from playwright.sync_api import sync_playwright
import time

def test_lesson2():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        page = browser.new_page()
        page.set_viewport_size({"width": 1200, "height": 800})

        print("🔍 Loading page...")
        page.goto("http://127.0.0.1:8011/?lesson=1", wait_until="networkidle")
        time.sleep(1)

        # First drag - "drag me to the SHOW box"
        print("\n🎯 Dragging 'drag me to the SHOW box'...")
        blue_tag = page.locator('.tag[data-tag="drag me to the SHOW box"]')
        tag_collection = page.locator('[data-zone-type="union"] .tag-collection').first
        blue_tag.drag_to(tag_collection)
        time.sleep(2)

        cards = page.locator('.card-item').all()
        print(f"After drag 1: {len(cards)} cards visible")
        for i, card in enumerate(cards):
            title = card.locator('.card-title').inner_text()
            print(f"  Card {i+1}: {title}")

        # Second drag - "drag me next"
        print("\n🎯 Dragging 'drag me next'...")
        next_tag = page.locator('.tag[data-tag="drag me next"]')
        next_tag.drag_to(tag_collection)
        time.sleep(2)

        # Check tags in union zone
        tags_in_zone = page.locator('[data-zone-type="union"] .tag').all()
        print(f"\nTags in SHOW zone: {len(tags_in_zone)}")
        for i, tag in enumerate(tags_in_zone):
            print(f"  Tag {i+1}: {tag.inner_text()}")

        # Check cards
        cards_after = page.locator('.card-item').all()
        print(f"\nAfter drag 2: {len(cards_after)} cards visible")
        for i, card in enumerate(cards_after):
            title = card.locator('.card-title').inner_text()
            print(f"  Card {i+1}: {title}")

        # Check API request
        print("\n📋 Checking last API request...")

        print("\n⏸️  Browser open for inspection (15s)...")
        time.sleep(15)

        browser.close()

if __name__ == "__main__":
    test_lesson2()
