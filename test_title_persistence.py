#!/usr/bin/env python3
"""Test card title persistence as described by user."""

import asyncio
from playwright.async_api import async_playwright

async def test_title_persistence():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        page = await browser.new_page(viewport={'width': 1680, 'height': 1050})

        print("1. Opening MultiCardz...")
        await page.goto('http://localhost:8011')
        await page.wait_for_load_state('networkidle')

        print("2. Dragging tag1 to SHOW zone...")
        # Find tag1
        tag1 = await page.wait_for_selector('.tag[data-tag="tag1"]', timeout=10000)
        # Find union zone (SHOW)
        show_zone = await page.wait_for_selector('[data-zone-type="union"]', timeout=10000)

        # Drag tag1 to show zone
        await page.drag_and_drop('.tag[data-tag="tag1"]', '[data-zone-type="union"]')
        await page.wait_for_timeout(1000)

        print("3. Waiting for cards to render...")
        await page.wait_for_selector('.card-item', timeout=10000)

        # Get first card
        cards = await page.query_selector_all('.card-item')
        print(f"   Found {len(cards)} cards")

        card_title = await cards[0].query_selector('.card-title')
        original_title = await card_title.text_content()
        print(f"   Original title: {original_title}")

        print("4. Changing card title...")

        # Listen to console messages
        page.on('console', lambda msg: print(f"   [CONSOLE] {msg.text}"))

        # Triple click to select all text in contenteditable
        await card_title.click(click_count=3)
        await page.wait_for_timeout(100)
        await page.keyboard.type('Test Persistence Title')
        await page.wait_for_timeout(100)
        # Click outside to trigger blur
        await page.click('body')
        await page.wait_for_timeout(2000)  # Wait for API call

        print("5. Refreshing page...")
        await page.reload()
        await page.wait_for_load_state('networkidle')

        print("6. Dragging tag1 to SHOW zone again...")
        tag1_after = await page.wait_for_selector('.tag[data-tag="tag1"]', timeout=10000)
        show_zone_after = await page.wait_for_selector('[data-zone-type="union"]', timeout=10000)
        await page.drag_and_drop('.tag[data-tag="tag1"]', '[data-zone-type="union"]')
        await page.wait_for_timeout(1000)

        print("7. Checking if title persisted...")
        await page.wait_for_selector('.card-item', timeout=10000)

        # Debug: Check HTML structure
        first_card_html = await page.eval_on_selector('.card-item', 'el => el.outerHTML')
        print(f"   First card HTML: {first_card_html[:500]}")

        cards_after = await page.query_selector_all('.card-item')
        card_title_after = await cards_after[0].query_selector('.card-title')
        new_title = await card_title_after.text_content()
        print(f"   Title after refresh: {new_title}")

        if new_title == 'Test Persistence Title':
            print("✅ SUCCESS: Title persisted!")
        else:
            print(f"❌ FAILURE: Title did NOT persist. Expected 'Test Persistence Title', got '{new_title}'")

        await browser.close()

asyncio.run(test_title_persistence())
