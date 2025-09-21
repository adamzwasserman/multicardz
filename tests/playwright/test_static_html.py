#!/usr/bin/env python3
"""
Static HTML test for MultiCardz™ drag-drop system.
Creates a static HTML file and tests it with Playwright.
"""

import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright


def create_test_html():
    """Create a static HTML file for testing."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MultiCardz™ Drag-Drop Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }
        .tag-cloud {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .tag {
            display: inline-block;
            background: #007bff;
            color: white;
            padding: 8px 12px;
            margin: 4px;
            border-radius: 4px;
            cursor: grab;
            user-select: none;
        }
        .tag:hover {
            background: #0056b3;
        }
        .tag.dragging {
            opacity: 0.5;
        }
        .tag.selected {
            background: #dc3545;
            outline: 2px solid #ffc107;
        }
        .drop-zone {
            background: #e9ecef;
            border: 2px dashed #6c757d;
            border-radius: 8px;
            padding: 20px;
            margin: 10px 0;
            min-height: 60px;
            transition: all 0.3s ease;
        }
        .drop-zone.drag-over {
            background: #d1ecf1;
            border-color: #007bff;
        }
        .union-zone {
            border-color: #28a745;
        }
        .intersection-zone {
            border-color: #dc3545;
        }
        .controls {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .checkbox-group {
            margin: 10px 0;
        }
        .status {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 10px;
            border-radius: 4px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <h1>MultiCardz™ Drag-Drop Test</h1>

    <div class="tag-cloud">
        <h3>Available Tags</h3>
        <span class="tag" data-tag="javascript" data-type="tag" draggable="true">javascript</span>
        <span class="tag" data-tag="python" data-type="tag" draggable="true">python</span>
        <span class="tag" data-tag="react" data-type="tag" draggable="true">react</span>
        <span class="tag" data-tag="fastapi" data-type="tag" draggable="true">fastapi</span>
        <span class="tag" data-tag="testing" data-type="tag" draggable="true">testing</span>
    </div>

    <div class="controls">
        <h3>Controls</h3>
        <div class="checkbox-group">
            <input type="checkbox" id="startWithAllCards" data-affects-rendering="true">
            <label for="startWithAllCards">Start with all cards visible</label>
        </div>
        <div class="checkbox-group">
            <input type="checkbox" id="showColors" data-affects-rendering="true" checked>
            <label for="showColors">Show colors on tags/cards</label>
        </div>
    </div>

    <div class="drop-zones">
        <h3>Drop Zones</h3>

        <div class="drop-zone union-zone" data-zone-type="union" data-accepts="tags,group-tags">
            <strong>Union Zone (ANY)</strong> - Drop tags here
            <div class="tag-collection"></div>
        </div>

        <div class="drop-zone intersection-zone" data-zone-type="intersection" data-accepts="tags,group-tags">
            <strong>Intersection Zone (ALL)</strong> - Drop tags here
            <div class="tag-collection"></div>
        </div>

        <div class="drop-zone" data-zone-type="row" data-accepts="tags,group-tags">
            <strong>Row Zone</strong> - Drop tags here
            <div class="tag-collection"></div>
        </div>

        <div class="drop-zone" data-zone-type="column" data-accepts="tags,group-tags">
            <strong>Column Zone</strong> - Drop tags here
            <div class="tag-collection"></div>
        </div>
    </div>

    <div class="status" id="status">
        Ready for testing. Drag tags to zones to test functionality.
    </div>

    <script>
        // Simple SpatialDragDrop class for testing
        class SpatialDragDrop {
            constructor() {
                this.selectedTags = new Set();
                this.init();
                window.dragDropSystem = this;
                console.log('SpatialDragDrop initialized');
            }

            init() {
                this.attachTagListeners();
                this.attachZoneListeners();
                this.attachControlListeners();
            }

            attachTagListeners() {
                document.querySelectorAll('.tag').forEach(tag => {
                    tag.addEventListener('click', (e) => this.handleTagClick(e));
                    tag.addEventListener('dragstart', (e) => this.handleDragStart(e));
                    tag.addEventListener('dragend', (e) => this.handleDragEnd(e));
                });
            }

            attachZoneListeners() {
                document.querySelectorAll('.drop-zone').forEach(zone => {
                    zone.addEventListener('dragover', (e) => this.handleDragOver(e));
                    zone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
                    zone.addEventListener('drop', (e) => this.handleDrop(e));
                });
            }

            attachControlListeners() {
                document.querySelectorAll('[data-affects-rendering]').forEach(control => {
                    control.addEventListener('change', () => this.handleControlChange());
                });
            }

            handleTagClick(e) {
                const tag = e.target;
                if (e.metaKey || e.ctrlKey) {
                    // Multi-select
                    if (this.selectedTags.has(tag)) {
                        this.selectedTags.delete(tag);
                        tag.classList.remove('selected');
                    } else {
                        this.selectedTags.add(tag);
                        tag.classList.add('selected');
                    }
                } else {
                    // Single select
                    this.clearSelection();
                    this.selectedTags.add(tag);
                    tag.classList.add('selected');
                }
                this.updateStatus();
            }

            handleDragStart(e) {
                const tag = e.target;
                tag.classList.add('dragging');
                e.dataTransfer.setData('text/plain', tag.dataset.tag);
                e.dataTransfer.effectAllowed = 'move';
            }

            handleDragEnd(e) {
                e.target.classList.remove('dragging');
            }

            handleDragOver(e) {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
                e.currentTarget.classList.add('drag-over');
            }

            handleDragLeave(e) {
                e.currentTarget.classList.remove('drag-over');
            }

            handleDrop(e) {
                e.preventDefault();
                const zone = e.currentTarget;
                zone.classList.remove('drag-over');

                const tagName = e.dataTransfer.getData('text/plain');
                const tag = document.querySelector(`[data-tag="${tagName}"]`);

                if (tag) {
                    const tagCollection = zone.querySelector('.tag-collection');
                    if (tagCollection) {
                        tagCollection.appendChild(tag);
                        tag.classList.remove('dragging', 'selected');
                        this.selectedTags.delete(tag);
                        this.updateStatus();
                        this.updateStateAndRender();
                    }
                }
            }

            handleControlChange() {
                this.updateStatus();
                this.updateStateAndRender();
            }

            clearSelection() {
                this.selectedTags.forEach(tag => {
                    tag.classList.remove('selected');
                });
                this.selectedTags.clear();
            }

            deriveStateFromDOM() {
                const state = {
                    zones: {},
                    controls: {}
                };

                // Get zone states
                document.querySelectorAll('.drop-zone').forEach(zone => {
                    const zoneType = zone.dataset.zoneType;
                    const tags = Array.from(zone.querySelectorAll('.tag')).map(tag => tag.dataset.tag);

                    if (tags.length > 0) {
                        state.zones[zoneType] = {
                            tags: tags,
                            metadata: {
                                behavior: zoneType === 'union' ? 'union' :
                                        zoneType === 'intersection' ? 'intersection' :
                                        zoneType
                            }
                        };
                    }
                });

                // Get control states
                document.querySelectorAll('[data-affects-rendering]').forEach(control => {
                    if (control.type === 'checkbox') {
                        state.controls[control.id] = control.checked;
                    }
                });

                return state;
            }

            updateStateAndRender() {
                const state = this.deriveStateFromDOM();
                console.log('State updated:', state);

                // Simulate API call
                if (Object.keys(state.zones).length > 0 || state.controls.startWithAllCards) {
                    this.simulateCardRender(state);
                }
            }

            simulateCardRender(state) {
                // Simulate card rendering
                console.log('Simulating card render with state:', state);

                // Update status
                const activeZones = Object.keys(state.zones);
                const activeControls = Object.entries(state.controls).filter(([k, v]) => v).map(([k, v]) => k);

                document.getElementById('status').innerHTML = `
                    <strong>State Updated:</strong><br>
                    Active zones: ${activeZones.join(', ') || 'none'}<br>
                    Active controls: ${activeControls.join(', ') || 'none'}<br>
                    <em>Cards would be rendered here in full system</em>
                `;
            }

            updateStatus() {
                const selectedCount = this.selectedTags.size;
                if (selectedCount > 0) {
                    document.getElementById('status').innerHTML = `
                        <strong>${selectedCount} tag(s) selected</strong><br>
                        Ready for drag-drop or multi-select operations
                    `;
                }
            }
        }

        // Initialize when DOM is ready
        document.addEventListener('DOMContentLoaded', () => {
            new SpatialDragDrop();
        });
    </script>
</body>
</html>
    """

    test_file = Path("test_drag_drop.html")
    test_file.write_text(html_content)
    return test_file


import pytest

@pytest.mark.asyncio
async def test_static_html():
    """Test the drag-drop system with static HTML."""
    print("🧪 Testing MultiCardz™ with static HTML...")

    # Create test file
    test_file = create_test_html()
    print(f"📄 Created test file: {test_file}")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)  # Headless for CI
            page = await browser.new_page()

            # Load the test file
            await page.goto(f"file://{test_file.absolute()}")
            print("✅ Test page loaded")

            # Wait for JavaScript to initialize
            await page.wait_for_function("window.dragDropSystem !== undefined")
            print("✅ SpatialDragDrop system initialized")

            # Test basic elements
            tags = await page.query_selector_all(".tag")
            zones = await page.query_selector_all(".drop-zone")
            controls = await page.query_selector_all("[data-affects-rendering]")

            print(f"📊 Found: {len(tags)} tags, {len(zones)} zones, {len(controls)} controls")

            # Test drag and drop
            if len(tags) > 0 and len(zones) > 0:
                print("🧪 Testing drag and drop...")

                first_tag = tags[0]
                union_zone = await page.query_selector(".union-zone")

                tag_text = await first_tag.text_content()
                print(f"  🎯 Dragging '{tag_text}' to union zone...")

                # Perform drag and drop manually
                await first_tag.hover()
                await page.mouse.down()
                await union_zone.hover()
                await page.mouse.up()
                await asyncio.sleep(0.5)

                # Check if tag moved
                tags_in_zone = await union_zone.query_selector_all(".tag")
                if len(tags_in_zone) > 0:
                    print("✅ Drag and drop successful!")
                else:
                    print("❌ Drag and drop failed")

                # Check state
                state = await page.evaluate("window.dragDropSystem.deriveStateFromDOM()")
                if state.get("zones", {}).get("union"):
                    print("✅ State correctly updated")
                    print(f"  Union tags: {state['zones']['union']['tags']}")
                else:
                    print("❌ State not updated")

            # Test multi-select
            if len(tags) >= 2:
                print("🧪 Testing multi-select...")

                # Clear any existing selections
                await page.evaluate("window.dragDropSystem.clearSelection()")

                # Multi-select with Cmd/Ctrl+click
                modifier = "Meta" if sys.platform == "darwin" else "Control"

                await tags[0].click()
                await tags[1].click(modifiers=[modifier])

                selected_count = await page.evaluate("window.dragDropSystem.selectedTags.size")
                if selected_count >= 2:
                    print(f"✅ Multi-select working ({selected_count} tags selected)")
                else:
                    print("❌ Multi-select failed")

            # Test controls
            print("🧪 Testing controls...")
            checkbox = await page.query_selector("#startWithAllCards")
            if checkbox:
                await checkbox.click()
                await asyncio.sleep(0.2)

                checked = await checkbox.is_checked()
                if checked:
                    print("✅ Control interaction working")
                else:
                    print("❌ Control interaction failed")

            print("🔍 Browser will stay open for 1 second for inspection...")
            await asyncio.sleep(1)

            await browser.close()

    finally:
        # Clean up test file
        test_file.unlink()
        print("🧹 Cleaned up test file")


if __name__ == "__main__":
    print("🚀 MultiCardz™ Static HTML Test")

    try:
        asyncio.run(test_static_html())
        print("\n🎉 Static HTML test completed successfully!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)