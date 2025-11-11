"""
DATAOS Compliance Tests for Drag-Drop System

Tests that verify DOM is the single source of truth with zero caching,
zero duplicate state, and perfect consistency during rapid operations.

BDD Feature: tests/features/dataos_compliance.feature
"""

import pytest
import time
from playwright.sync_api import Page, expect


@pytest.fixture
def setup_drag_drop_page(page: Page):
    """
    Set up a test page with drag-drop system and mock data.
    """
    # Navigate to a test page with the drag-drop system
    # This would be replaced with actual multicardz page URL
    page.goto("http://localhost:8011/")

    # Wait for drag-drop system to initialize
    page.wait_for_selector('[data-zone-type]')
    page.wait_for_function("window.dragDropSystem !== undefined")

    return page


class TestDeriveStateFromDOM:
    """
    Test that deriveStateFromDOM() always returns fresh data from DOM.
    """

    def test_returns_fresh_data_on_every_call(self, setup_drag_drop_page: Page):
        """
        Scenario: deriveStateFromDOM returns fresh data on every call
        """
        page = setup_drag_drop_page

        # Given: I have tags in multiple zones
        page.evaluate("""
            // Ensure we have some tags in zones for testing
            const includeZone = document.querySelector('[data-zone-type="include"]');
            const tag = document.querySelector('[data-tag]');
            if (includeZone && tag) {
                const collection = includeZone.querySelector('.tag-collection');
                if (collection) collection.appendChild(tag.cloneNode(true));
            }
        """)

        # When: I call deriveStateFromDOM() twice in rapid succession
        result = page.evaluate("""
            const start = performance.now();
            const state1 = window.dragDropSystem.deriveStateFromDOM();
            const state2 = window.dragDropSystem.deriveStateFromDOM();
            const duration = performance.now() - start;

            ({
                state1: JSON.stringify(state1),
                state2: JSON.stringify(state2),
                identical: JSON.stringify(state1) === JSON.stringify(state2),
                duration: duration
            })
        """)

        # Then: both calls should return identical fresh data
        assert result["identical"], "Both calls should return identical data"

        # And: execution time should be under 16ms
        assert result["duration"] < 16, f"Execution took {result['duration']}ms, should be <16ms"

    def test_no_state_cache_exists(self, setup_drag_drop_page: Page):
        """
        Scenario: No state cache exists after operations
        """
        page = setup_drag_drop_page

        # Given: I have performed multiple drag-drop operations
        # (system is already initialized)

        # When: I inspect the SpatialDragDrop instance
        cache_status = page.evaluate("""
            ({
                hasStateCache: window.dragDropSystem.hasOwnProperty('stateCache'),
                stateCacheValue: window.dragDropSystem.stateCache,
                hasCacheDuration: window.dragDropSystem.hasOwnProperty('CACHE_DURATION'),
                hasStateCacheTime: window.dragDropSystem.hasOwnProperty('stateCacheTime')
            })
        """)

        # Then: cache properties should not exist or be null/0
        # NOTE: These assertions will FAIL initially (RED phase) until violations are fixed
        assert not cache_status["hasStateCache"] or cache_status["stateCacheValue"] is None, \
            "stateCache should not exist or be null"
        assert not cache_status["hasCacheDuration"], \
            "CACHE_DURATION constant should not exist"
        assert not cache_status["hasStateCacheTime"] or cache_status.get("stateCacheTime") == 0, \
            "stateCacheTime should not exist or be 0"


class TestRapidOperations:
    """
    Test that rapid operations maintain perfect consistency.
    """

    def test_rapid_tag_movement_consistency(self, setup_drag_drop_page: Page):
        """
        Scenario: Rapid tag movements maintain consistency
        """
        page = setup_drag_drop_page

        # Given: I have a tag "JavaScript" in the user cloud
        page.evaluate("""
            // Ensure we have a test tag
            const cloud = document.querySelector('.cloud-user .tags-wrapper');
            if (cloud && !document.querySelector('[data-tag="JavaScript"]')) {
                const tag = document.createElement('span');
                tag.className = 'tag tag-cloud';
                tag.setAttribute('data-tag', 'JavaScript');
                tag.setAttribute('data-tag-id', 'test-js-123');
                tag.setAttribute('draggable', 'true');
                tag.textContent = 'JavaScript';
                cloud.appendChild(tag);
            }
        """)

        # When: I drag "JavaScript" to the "include" zone
        tag = page.locator('[data-tag="JavaScript"]')
        include_zone = page.locator('[data-zone-type="include"]')

        # Simulate drag-drop by directly manipulating DOM (faster than actual drag)
        page.evaluate("""
            const tag = document.querySelector('[data-tag="JavaScript"]');
            const includeZone = document.querySelector('[data-zone-type="include"]');
            const collection = includeZone.querySelector('.tag-collection');

            // Move tag to zone
            collection.appendChild(tag);
            tag.classList.remove('tag-cloud');
            tag.classList.add('tag-active');
        """)

        # And: I immediately query the system state (within 1ms)
        state = page.evaluate("""
            window.dragDropSystem.deriveStateFromDOM()
        """)

        # Then: the state should reflect "JavaScript" in the "include" zone
        include_tags = state.get("zones", {}).get("include", {}).get("tags", [])
        assert "JavaScript" in include_tags, \
            f"JavaScript should be in include zone, got tags: {include_tags}"

    def test_state_extraction_within_1ms(self, setup_drag_drop_page: Page):
        """
        Scenario: State extraction within 1ms after DOM mutation
        """
        page = setup_drag_drop_page

        # When: I programmatically move a tag and query within 1ms
        result = page.evaluate("""
            const tag = document.querySelector('[data-tag]');
            const includeZone = document.querySelector('[data-zone-type="include"]');

            if (tag && includeZone) {
                const collection = includeZone.querySelector('.tag-collection');
                const tagName = tag.getAttribute('data-tag');

                // Move tag
                collection.appendChild(tag);
                tag.classList.add('tag-active');

                // Query state immediately (< 1ms)
                const state = window.dragDropSystem.deriveStateFromDOM();

                // Check if tag is in the include zone
                const includeTagNames = state.zones?.include?.tags || [];

                return {
                    tagName: tagName,
                    foundInInclude: includeTagNames.includes(tagName),
                    includeTagsCount: includeTagNames.length
                };
            }
            return { error: 'Tag or zone not found' };
        """)

        # Then: the state should reflect the new DOM position immediately
        assert result.get("foundInInclude"), \
            f"Tag {result.get('tagName')} should be found in include zone immediately"


class TestSelectionState:
    """
    Test that selection state is derived from DOM, not JavaScript variables.
    """

    def test_selection_derived_from_dom(self, setup_drag_drop_page: Page):
        """
        Scenario: selectedTags derived from DOM not JavaScript Set
        """
        page = setup_drag_drop_page

        # Given: I have selected 5 tags using Ctrl+click
        page.evaluate("""
            const tags = Array.from(document.querySelectorAll('[data-tag]')).slice(0, 5);
            tags.forEach(tag => {
                tag.classList.add('tag-selected');
                tag.setAttribute('aria-selected', 'true');
            });
        """)

        # When: I query the selection state
        selection_state = page.evaluate("""
            const selectedInDOM = document.querySelectorAll('[data-tag].tag-selected').length;
            const hasSelectedTagsSet = window.dragDropSystem.hasOwnProperty('selectedTags');
            const hasSelectionStateObj = window.dragDropSystem.hasOwnProperty('selectionState');

            return {
                domSelectedCount: selectedInDOM,
                hasSelectedTagsSet: hasSelectedTagsSet,
                hasSelectionStateObj: hasSelectionStateObj
            };
        """)

        # Then: selection should be read from DOM
        assert selection_state["domSelectedCount"] == 5, "Should have 5 selected tags in DOM"

        # And: no JavaScript Set should exist (will FAIL initially - RED phase)
        # NOTE: These assertions will fail until violations are fixed
        assert not selection_state["hasSelectedTagsSet"], \
            "selectedTags Set should not exist - use DOM .tag-selected classes"
        assert not selection_state["hasSelectionStateObj"], \
            "selectionState object should not exist - use DOM queries"

    def test_dragged_elements_from_dom(self, setup_drag_drop_page: Page):
        """
        Scenario: draggedElements derived from DOM not JavaScript array
        """
        page = setup_drag_drop_page

        # Given: I start dragging 3 selected tags
        page.evaluate("""
            const tags = Array.from(document.querySelectorAll('[data-tag]')).slice(0, 3);
            tags.forEach(tag => {
                tag.classList.add('dragging');
                tag.setAttribute('aria-grabbed', 'true');
            });
        """)

        # When: the system needs to know what's being dragged
        drag_state = page.evaluate("""
            const draggingInDOM = document.querySelectorAll('[data-tag].dragging').length;
            const hasDraggedElementsArray = window.dragDropSystem.hasOwnProperty('draggedElements');
            const draggedElementsValue = window.dragDropSystem.draggedElements;

            return {
                domDraggingCount: draggingInDOM,
                hasDraggedElementsArray: hasDraggedElementsArray,
                draggedElementsLength: Array.isArray(draggedElementsValue) ? draggedElementsValue.length : 0
            };
        """)

        # Then: it should query DOM for .dragging classes
        assert drag_state["domDraggingCount"] == 3, "Should have 3 dragging tags in DOM"

        # And: no JavaScript array should store references (will FAIL - RED phase)
        assert not drag_state["hasDraggedElementsArray"] or drag_state["draggedElementsLength"] == 0, \
            "draggedElements array should not exist or be empty - use DOM .dragging classes"


class TestNoStateObjects:
    """
    Test that no state objects exist - all state from DOM.
    """

    def test_no_selection_state_object(self, setup_drag_drop_page: Page):
        """
        Scenario: No selectionState object exists
        """
        page = setup_drag_drop_page

        # When: I inspect the SpatialDragDrop instance
        state_props = page.evaluate("""
            ({
                hasSelectionState: window.dragDropSystem.hasOwnProperty('selectionState'),
                hasSelectedTags: window.dragDropSystem.hasOwnProperty('selectedTags'),
                hasAnchorTag: window.dragDropSystem.selectionState?.anchorTag !== undefined,
                hasLastSelectedTag: window.dragDropSystem.selectionState?.lastSelectedTag !== undefined
            })
        """)

        # Then: no state objects should exist (will FAIL - RED phase)
        assert not state_props["hasSelectionState"], \
            "selectionState object should not exist"
        assert not state_props["hasSelectedTags"], \
            "selectedTags Set should not exist"

    def test_ghost_canvas_cleanup(self, setup_drag_drop_page: Page):
        """
        Scenario: Ghost image canvas cleanup doesn't cache state
        """
        page = setup_drag_drop_page

        # Given: I have dragged multiple tags (simulate completed drag)
        page.evaluate("""
            // Simulate drag operation that might create ghost canvas
            const tags = Array.from(document.querySelectorAll('[data-tag]')).slice(0, 3);
            if (window.dragDropSystem.generateGhostImage) {
                window.dragDropSystem.generateGhostImage(new Set(tags));
            }
            // Simulate cleanup
            if (window.dragDropSystem.cleanupGhostImage) {
                window.dragDropSystem.cleanupGhostImage();
            }
        """)

        # When: the drag operation completes
        ghost_state = page.evaluate("""
            ({
                hasCurrentGhostCanvas: window.dragDropSystem.hasOwnProperty('currentGhostCanvas'),
                currentGhostCanvasValue: window.dragDropSystem.currentGhostCanvas,
                hasCurrentGhostImage: window.dragDropSystem.hasOwnProperty('currentGhostImage'),
                currentGhostImageValue: window.dragDropSystem.currentGhostImage
            })
        """)

        # Then: no ghost references should remain (will FAIL initially - RED phase)
        assert not ghost_state["hasCurrentGhostCanvas"] or ghost_state["currentGhostCanvasValue"] is None, \
            "currentGhostCanvas should not exist or be null"
        assert not ghost_state["hasCurrentGhostImage"] or ghost_state["currentGhostImageValue"] is None, \
            "currentGhostImage should not exist or be null"


class TestPerformance:
    """
    Test that performance is maintained without caching.
    """

    def test_performance_without_caching(self, setup_drag_drop_page: Page):
        """
        Scenario: Performance maintained without caching
        """
        page = setup_drag_drop_page

        # Given: I have tags in zones
        # When: I call deriveStateFromDOM() 10 times in sequence
        result = page.evaluate("""
            const durations = [];
            const states = [];

            for (let i = 0; i < 10; i++) {
                const start = performance.now();
                const state = window.dragDropSystem.deriveStateFromDOM();
                const duration = performance.now() - start;
                durations.push(duration);
                states.push(JSON.stringify(state));
            }

            // Check all states are identical
            const allIdentical = states.every(s => s === states[0]);
            const maxDuration = Math.max(...durations);
            const avgDuration = durations.reduce((a, b) => a + b, 0) / durations.length;

            return {
                allIdentical: allIdentical,
                maxDuration: maxDuration,
                avgDuration: avgDuration,
                durations: durations
            };
        """)

        # Then: each call should complete in under 10ms
        assert result["maxDuration"] < 10, \
            f"Max duration {result['maxDuration']}ms exceeds 10ms threshold"

        # And: all calls should return identical data
        assert result["allIdentical"], "All state calls should return identical data"

    def test_no_invalidate_cache_method(self, setup_drag_drop_page: Page):
        """
        Scenario: No invalidateCache method exists
        """
        page = setup_drag_drop_page

        # When: I inspect the SpatialDragDrop prototype
        has_cache_method = page.evaluate("""
            typeof window.dragDropSystem.invalidateCache === 'function'
        """)

        # Then: no invalidateCache method should exist (will FAIL - RED phase)
        assert not has_cache_method, \
            "invalidateCache method should not exist - no caching should occur"


class TestRapidMultiSelection:
    """
    Test state consistency during rapid multi-selection operations.
    """

    def test_rapid_shift_click_consistency(self, setup_drag_drop_page: Page):
        """
        Scenario: State consistency during rapid multi-selection
        """
        page = setup_drag_drop_page

        # Given: I have 20 tags visible
        page.evaluate("""
            const cloud = document.querySelector('.cloud-user .tags-wrapper');
            // Ensure we have at least 20 tags for testing
            for (let i = 0; i < 20; i++) {
                if (!document.querySelector(`[data-tag="tag-${i}"]`)) {
                    const tag = document.createElement('span');
                    tag.className = 'tag tag-cloud';
                    tag.setAttribute('data-tag', `tag-${i}`);
                    tag.setAttribute('data-tag-id', `id-${i}`);
                    tag.setAttribute('draggable', 'true');
                    tag.textContent = `tag-${i}`;
                    cloud.appendChild(tag);
                }
            }
        """)

        # When: I rapidly select 10 tags
        result = page.evaluate("""
            const tags = Array.from(document.querySelectorAll('[data-tag]')).slice(0, 10);
            const selectionStates = [];

            // Rapidly select tags
            tags.forEach((tag, index) => {
                tag.classList.add('tag-selected');
                tag.setAttribute('aria-selected', 'true');

                // Query selection state after each click
                const selectedCount = document.querySelectorAll('[data-tag].tag-selected').length;
                selectionStates.push(selectedCount);
            });

            return {
                selectionProgression: selectionStates,
                finalCount: document.querySelectorAll('[data-tag].tag-selected').length
            };
        """)

        # Then: final selection should match exactly what's in the DOM
        assert result["finalCount"] == 10, \
            f"Should have 10 selected tags, got {result['finalCount']}"

        # And: selection should have progressed correctly (1, 2, 3, ... 10)
        expected_progression = list(range(1, 11))
        assert result["selectionProgression"] == expected_progression, \
            f"Selection should progress 1-10, got {result['selectionProgression']}"


class TestConcurrentOperations:
    """
    Test that concurrent operations maintain DOM authority.
    """

    def test_concurrent_dom_modifications(self, setup_drag_drop_page: Page):
        """
        Scenario: Concurrent operations maintain DOM authority
        """
        page = setup_drag_drop_page

        # Given: I have two rapid operations happening
        result = page.evaluate("""
            const tag = document.querySelector('[data-tag]');
            const includeZone = document.querySelector('[data-zone-type="include"]');
            const excludeZone = document.querySelector('[data-zone-type="exclude"]');

            if (tag && includeZone && excludeZone) {
                const tagName = tag.getAttribute('data-tag');
                const includeCollection = includeZone.querySelector('.tag-collection');

                // Operation 1: Move to include zone
                includeCollection.appendChild(tag);

                // Operation 2: Query state immediately (before first completes)
                const state1 = window.dragDropSystem.deriveStateFromDOM();

                // Operation 1 "completes" (add class)
                tag.classList.add('tag-active');

                // Query again
                const state2 = window.dragDropSystem.deriveStateFromDOM();

                return {
                    tagName: tagName,
                    state1IncludeTags: state1.zones?.include?.tags || [],
                    state2IncludeTags: state2.zones?.include?.tags || [],
                    bothReflectDom: true
                };
            }
            return { error: 'Setup failed' };
        """)

        # Then: both queries should reflect actual DOM state at query time
        assert result.get("tagName") in result.get("state1IncludeTags", []), \
            "State should reflect DOM immediately after DOM mutation"
        assert result.get("tagName") in result.get("state2IncludeTags", []), \
            "State should continue to reflect DOM on subsequent queries"
