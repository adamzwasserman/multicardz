#!/usr/bin/env python3
"""Quick test card layout."""

from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.set_viewport_size({"width": 1200, "height": 800})

    page.goto("http://127.0.0.1:8011/?lesson=1", wait_until="networkidle")

    # Drag blue tag to SHOW zone
    blue_tag = page.locator('.tag[data-tag="drag me to the SHOW box"]')
    show_zone = page.locator('[data-zone-type="union"] .tag-collection').first
    blue_tag.drag_to(show_zone)
    time.sleep(2)

    # Check cards
    cards = page.locator('.card-item').all()
    print(f"📇 Cards visible: {len(cards)}")

    if len(cards) >= 2:
        box1 = cards[0].bounding_box()
        box2 = cards[1].bounding_box()
        print(f"Card 1: x={box1['x']:.0f}, y={box1['y']:.0f}")
        print(f"Card 2: x={box2['x']:.0f}, y={box2['y']:.0f}")

        y_diff = abs(box1['y'] - box2['y'])
        if y_diff < 10:
            print(f"✅ SAME row (y diff: {y_diff:.0f}px)")
        else:
            print(f"❌ DIFFERENT rows (y diff: {y_diff:.0f}px)")

    # Check styles
    card_display = page.locator('.card-display').first
    styles = card_display.evaluate('el => getComputedStyle(el).flexDirection')
    print(f"flex-direction: {styles}")

    browser.close()
