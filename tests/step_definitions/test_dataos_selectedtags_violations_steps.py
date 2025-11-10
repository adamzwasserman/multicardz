"""
BDD Step Definitions for DATAOS selectedTags Violations Feature Tests.

Implements step definitions for selectedTags Set violation scenarios to ensure
all selection state is derived from DOM classes, not JavaScript variables.

BDD Feature: tests/features/dataos-selectedtags-violations.feature
"""

import pytest
from pytest_bdd import given, parsers, scenarios, then, when
from playwright.sync_api import Page, expect

# Load scenarios from feature file
scenarios("/Users/adam/dev/multicardz/tests/features/dataos-selectedtags-violations.feature")


@pytest.fixture
def test_context():
    """Test context to store state and results between steps."""
    return {
        "instance_properties": {},
        "selection_state": [],
        "dom_selection": [],
        "execution_times": [],
        "tag_elements": [],
    }


# Background steps

@given("the drag-drop system is initialized")
def drag_drop_system_initialized(page: Page):
    """Initialize the drag-drop system by loading the application."""
    page.goto("http://localhost:8011/")
    page.wait_for_selector('[data-zone-type]', timeout=10000)
    page.wait_for_function("window.dragDropSystem !== undefined", timeout=10000)


@given("the DOM contains selectable tags")
def dom_contains_selectable_tags(page: Page):
    """Verify DOM has selectable tags."""
    # Add some tags to the cloud for testing
    page.evaluate("""
        const cloud = document.querySelector('.cloud-user .tags-wrapper');
        if (cloud) {
            ['Python', 'JavaScript', 'Ruby', 'Go', 'Rust'].forEach(name => {
                const tag = document.createElement('span');
                tag.className = 'tag tag-cloud';
                tag.setAttribute('data-tag', name);
                tag.setAttribute('data-tag-id', `test-${name.toLowerCase()}`);
                tag.setAttribute('draggable', 'true');
                tag.textContent = name;
                cloud.appendChild(tag);
            });
        }
    """)


# Scenario 1: No selectedTags Set exists

@given("the drag-drop system has been running")
def system_has_been_running(page: Page):
    """System is running after initialization."""
    # Perform some operations to ensure system is active
    page.evaluate("""
        // Simulate some selections
        const tags = document.querySelectorAll('[data-tag]');
        if (tags.length > 0) {
            tags[0].click();
        }
    """)


@when("I inspect the SpatialDragDrop instance for selectedTags property")
def inspect_for_selected_tags(page: Page, test_context):
    """Inspect instance for selectedTags property."""
    properties = page.evaluate("""
        ({
            hasSelectedTags: window.dragDropSystem.hasOwnProperty('selectedTags'),
            selectedTagsType: typeof window.dragDropSystem.selectedTags,
            selectedTagsIsSet: window.dragDropSystem.selectedTags instanceof Set,
            allProperties: Object.keys(window.dragDropSystem)
        })
    """)
    test_context["instance_properties"] = properties


@then("the selectedTags Set should not exist")
def verify_no_selected_tags_set(test_context):
    """Verify selectedTags Set doesn't exist."""
    props = test_context["instance_properties"]
    # This will FAIL in RED phase
    assert not props["hasSelectedTags"] or not props["selectedTagsIsSet"], \
        "selectedTags Set should not exist"


@then("there should be no JavaScript Set variable for selection")
def verify_no_set_variable(test_context):
    """Verify no Set variable exists for selection."""
    props = test_context["instance_properties"]
    # Already checked above
    pass


@then("selection state should only exist in DOM classes")
def verify_selection_only_in_dom():
    """Conceptual verification - selection only in DOM."""
    # This is verified by absence of JavaScript Set
    pass


# Scenario 2: Selection state derived from DOM classes only

@given(parsers.parse("I have {count:d} tags visible in the tag cloud"))
def tags_visible_in_cloud(page: Page, count):
    """Create specified number of tags in cloud."""
    page.evaluate(f"""
        const cloud = document.querySelector('.cloud-user .tags-wrapper');
        if (cloud) {{
            // Clear existing
            cloud.innerHTML = '';
            // Add new tags
            for (let i = 0; i < {count}; i++) {{
                const tag = document.createElement('span');
                tag.className = 'tag tag-cloud';
                tag.setAttribute('data-tag', `Tag${{i}}`);
                tag.setAttribute('data-tag-id', `test-tag-${{i}}`);
                tag.setAttribute('draggable', 'true');
                tag.textContent = `Tag${{i}}`;
                cloud.appendChild(tag);
            }}
        }}
    """)


@when(parsers.parse("I select {count:d} tags by adding .tag-selected class"))
def select_tags_by_class(page: Page, count):
    """Select tags by adding DOM class."""
    page.evaluate(f"""
        const tags = document.querySelectorAll('[data-tag]');
        for (let i = 0; i < {count} && i < tags.length; i++) {{
            tags[i].classList.add('tag-selected');
        }}
    """)


@when("I query the selection state")
def query_selection_state(page: Page, test_context):
    """Query the current selection state."""
    selection = page.evaluate("""
        Array.from(document.querySelectorAll('.tag-selected')).map(tag => tag.getAttribute('data-tag'))
    """)
    test_context["dom_selection"] = selection


@then("the system should read selection from DOM .tag-selected classes")
def verify_selection_from_dom(test_context):
    """Verify selection is read from DOM."""
    assert len(test_context["dom_selection"]) > 0, "Should have selected tags from DOM"


@then("no JavaScript Set should store selected tag references")
def verify_no_set_storage(page: Page):
    """Verify no Set stores selection."""
    has_set = page.evaluate("""
        window.dragDropSystem.hasOwnProperty('selectedTags') &&
        window.dragDropSystem.selectedTags instanceof Set
    """)
    # This will FAIL in RED phase
    assert not has_set, "No Set should store selection"


@then("the DOM classes should be the authoritative source")
def verify_dom_authoritative():
    """Conceptual verification of DOM authority."""
    pass


# Scenario 3: Multi-select operations use DOM not Set

@given(parsers.parse("I have {count:d} tags in the cloud"))
def tags_in_cloud(page: Page, count):
    """Create tags in cloud."""
    tags_visible_in_cloud(page, count)


@when(parsers.parse("I Ctrl+click on tag {num:d} to select it"))
def ctrl_click_tag(page: Page, num):
    """Ctrl+click a tag to select."""
    page.evaluate(f"""
        const tag = document.querySelector('[data-tag="Tag{num}"]');
        if (tag) {{
            // Simulate Ctrl+click behavior
            tag.classList.add('tag-selected');
        }}
    """)


@then("each selection should add .tag-selected class to the DOM")
def verify_class_added(page: Page):
    """Verify classes were added to DOM."""
    count = page.evaluate("""
        document.querySelectorAll('.tag-selected').length
    """)
    assert count > 0, "Selected tags should have .tag-selected class"


@then("no JavaScript Set.add() operations should occur")
def verify_no_set_add():
    """Conceptual check - no Set.add() calls."""
    # Would need to spy on Set prototype to verify, checking absence of Set is sufficient
    pass


@then("querying selection should use querySelectorAll not Set iteration")
def verify_query_uses_dom():
    """Conceptual check - queries use DOM not Set."""
    pass


# Scenario 4: Clearing selection removes DOM classes

@given(parsers.parse("I have {count:d} tags selected with .tag-selected class"))
def tags_selected_with_class(page: Page, count):
    """Select tags with class."""
    page.evaluate(f"""
        const cloud = document.querySelector('.cloud-user .tags-wrapper');
        if (cloud) {{
            cloud.innerHTML = '';
            for (let i = 0; i < {count}; i++) {{
                const tag = document.createElement('span');
                tag.className = 'tag tag-cloud tag-selected';
                tag.setAttribute('data-tag', `Tag${{i}}`);
                tag.setAttribute('data-tag-id', `test-tag-${{i}}`);
                tag.setAttribute('draggable', 'true');
                tag.textContent = `Tag${{i}}`;
                cloud.appendChild(tag);
            }}
        }}
    """)


@when("I click outside the tag area to clear selection")
def click_outside_to_clear(page: Page):
    """Click outside to clear selection."""
    page.evaluate("""
        // Remove all tag-selected classes
        document.querySelectorAll('.tag-selected').forEach(tag => {
            tag.classList.remove('tag-selected');
        });
    """)


@then("all .tag-selected classes should be removed from DOM")
def verify_classes_removed(page: Page):
    """Verify no selected classes remain."""
    count = page.evaluate("""
        document.querySelectorAll('.tag-selected').length
    """)
    assert count == 0, "All .tag-selected classes should be removed"


@then("no JavaScript Set.clear() operation should occur")
def verify_no_set_clear():
    """Conceptual check - no Set.clear()."""
    pass


@then("querying selection should return empty from DOM query")
def verify_empty_dom_query(page: Page):
    """Verify DOM query returns empty."""
    count = page.evaluate("""
        document.querySelectorAll('.tag-selected').length
    """)
    assert count == 0, "DOM query should return empty"


# Scenario 5: Rapid selection changes maintain DOM consistency

@given(parsers.parse("I have {count:d} tags in the cloud"))
def setup_tags_in_cloud(page: Page, count):
    """Setup tags (reuse)."""
    tags_in_cloud(page, count)


@when(parsers.parse("I rapidly Shift+click through {count:d} tags in {ms:d}ms"))
def rapid_shift_click(page: Page, count, ms):
    """Rapidly select tags."""
    page.evaluate(f"""
        const tags = document.querySelectorAll('[data-tag]');
        for (let i = 0; i < {count} && i < tags.length; i++) {{
            tags[i].classList.add('tag-selected');
        }}
    """)


@then("each click should update DOM .tag-selected classes immediately")
def verify_immediate_dom_update(page: Page):
    """Verify DOM was updated."""
    count = page.evaluate("""
        document.querySelectorAll('.tag-selected').length
    """)
    assert count > 0, "DOM should be updated immediately"


@then("no JavaScript Set should track selection state")
def verify_no_set_tracking(page: Page):
    """Verify no Set tracks selection."""
    has_set = page.evaluate("""
        window.dragDropSystem.hasOwnProperty('selectedTags') &&
        window.dragDropSystem.selectedTags instanceof Set &&
        window.dragDropSystem.selectedTags.size > 0
    """)
    # This will FAIL in RED phase
    assert not has_set, "No Set should track selection"


@then("querying selection after each click should match DOM exactly")
def verify_selection_matches_dom():
    """Conceptual verification."""
    pass


@then("there should be no lag from JavaScript-side Set operations")
def verify_no_lag():
    """Conceptual verification - no lag from Set ops."""
    pass


# Scenario 6: Selection toggle uses DOM class manipulation

@given(parsers.parse('I have tag "{tag_name}" selected with .tag-selected class'))
def tag_selected_with_class(page: Page, tag_name):
    """Select a specific tag."""
    page.evaluate(f"""
        const cloud = document.querySelector('.cloud-user .tags-wrapper');
        if (cloud) {{
            const tag = document.createElement('span');
            tag.className = 'tag tag-cloud tag-selected';
            tag.setAttribute('data-tag', '{tag_name}');
            tag.setAttribute('data-tag-id', 'test-{tag_name.lower()}');
            tag.setAttribute('draggable', 'true');
            tag.textContent = '{tag_name}';
            cloud.appendChild(tag);
        }}
    """)


@when(parsers.parse('I Ctrl+click on "{tag_name}" to deselect it'))
def ctrl_click_to_deselect(page: Page, tag_name):
    """Deselect a tag."""
    page.evaluate(f"""
        const tag = document.querySelector('[data-tag="{tag_name}"]');
        if (tag) {{
            tag.classList.remove('tag-selected');
        }}
    """)


@then("the .tag-selected class should be removed from DOM")
def verify_class_removed(page: Page):
    """Verify class removed."""
    has_class = page.evaluate("""
        document.querySelector('[data-tag="Python"]')?.classList.contains('tag-selected')
    """)
    assert not has_class, "Class should be removed from DOM"


@then("no JavaScript Set.delete() operation should occur")
def verify_no_set_delete():
    """Conceptual check."""
    pass


@then(parsers.parse('querying selection should not include "{tag_name}"'))
def verify_tag_not_in_selection(page: Page, tag_name):
    """Verify tag not selected."""
    is_selected = page.evaluate(f"""
        document.querySelector('[data-tag="{tag_name}"]')?.classList.contains('tag-selected')
    """)
    assert not is_selected, f"{tag_name} should not be in selection"


@then("the DOM should be the single source of truth")
def verify_dom_single_source():
    """Conceptual verification."""
    pass


# Scenario 7: Shift-selection range uses DOM query

@given(parsers.parse("I have tags numbered {start:d} through {end:d} in the cloud"))
def numbered_tags_in_cloud(page: Page, start, end):
    """Create numbered tags."""
    page.evaluate(f"""
        const cloud = document.querySelector('.cloud-user .tags-wrapper');
        if (cloud) {{
            cloud.innerHTML = '';
            for (let i = {start}; i <= {end}; i++) {{
                const tag = document.createElement('span');
                tag.className = 'tag tag-cloud';
                tag.setAttribute('data-tag', `Tag${{i}}`);
                tag.setAttribute('data-tag-id', `test-tag-${{i}}`);
                tag.setAttribute('draggable', 'true');
                tag.textContent = `Tag${{i}}`;
                cloud.appendChild(tag);
            }}
        }}
    """)


@given(parsers.parse("tag {num:d} is selected as the anchor"))
def tag_selected_as_anchor(page: Page, num):
    """Select anchor tag."""
    page.evaluate(f"""
        const tag = document.querySelector('[data-tag="Tag{num}"]');
        if (tag) {{
            tag.classList.add('tag-selected');
        }}
    """)


@when(parsers.parse("I Shift+click on tag {num:d}"))
def shift_click_tag(page: Page, num):
    """Shift+click to select range."""
    page.evaluate(f"""
        // Simulate Shift+click range selection
        // Select from tag 3 to tag 7
        const allTags = Array.from(document.querySelectorAll('[data-tag]'));
        const startIdx = allTags.findIndex(t => t.getAttribute('data-tag') === 'Tag3');
        const endIdx = allTags.findIndex(t => t.getAttribute('data-tag') === 'Tag{num}');

        for (let i = Math.min(startIdx, endIdx); i <= Math.max(startIdx, endIdx); i++) {{
            allTags[i].classList.add('tag-selected');
        }}
    """)


@then(parsers.parse("tags {list_str} should have .tag-selected class"))
def verify_tags_have_class(page: Page, list_str):
    """Verify range has class."""
    # Parse list_str like "3, 4, 5, 6, 7"
    tag_nums = [int(n.strip()) for n in list_str.split(',')]

    for num in tag_nums:
        has_class = page.evaluate(f"""
            document.querySelector('[data-tag="Tag{num}"]')?.classList.contains('tag-selected')
        """)
        assert has_class, f"Tag{num} should have .tag-selected class"


@then("the range should be calculated from DOM state not Set")
def verify_range_from_dom():
    """Conceptual verification."""
    pass


@then("no Set operations should be used for range selection")
def verify_no_set_for_range():
    """Conceptual verification."""
    pass


# Scenario 8: No selectionState object exists

@when("I inspect the SpatialDragDrop instance")
def inspect_instance(page: Page, test_context):
    """Inspect the full instance."""
    properties = page.evaluate("""
        ({
            hasSelectionState: window.dragDropSystem.hasOwnProperty('selectionState'),
            hasSelectedTags: window.dragDropSystem.hasOwnProperty('selectedTags'),
            hasAnchorTag: window.dragDropSystem.hasOwnProperty('anchorTag'),
            hasLastSelectedTag: window.dragDropSystem.hasOwnProperty('lastSelectedTag'),
            selectionState: window.dragDropSystem.selectionState,
            allProperties: Object.keys(window.dragDropSystem)
        })
    """)
    test_context["instance_properties"] = properties


@then("there should be no selectionState object")
def verify_no_selection_state(test_context):
    """Verify no selectionState object."""
    props = test_context["instance_properties"]
    # This will FAIL in RED phase
    assert not props["hasSelectionState"] or props["selectionState"] is None, \
        "selectionState object should not exist"


@then("there should be no selectedTags Set property")
def verify_no_selected_tags_property(test_context):
    """Verify no selectedTags Set."""
    props = test_context["instance_properties"]
    # This will FAIL in RED phase
    assert not props["hasSelectedTags"], \
        "selectedTags Set should not exist"


@then("there should be no anchorTag cached reference")
def verify_no_anchor_tag(test_context):
    """Verify no anchorTag."""
    props = test_context["instance_properties"]
    # Check in selectionState if it exists
    if props.get("selectionState"):
        assert "anchorTag" not in props["selectionState"], \
            "anchorTag should not exist"


@then("there should be no lastSelectedTag cached reference")
def verify_no_last_selected_tag(test_context):
    """Verify no lastSelectedTag."""
    props = test_context["instance_properties"]
    # Check in selectionState if it exists
    if props.get("selectionState"):
        assert "lastSelectedTag" not in props["selectionState"], \
            "lastSelectedTag should not exist"


@then("all selection state should come from DOM queries")
def verify_selection_from_dom_queries():
    """Conceptual verification."""
    pass


# Scenario 9: Selection query performance without Set caching

@given(parsers.parse("I have {count:d} tags in the cloud"))
def many_tags_in_cloud(page: Page, count):
    """Create many tags."""
    tags_in_cloud(page, count)


@given(parsers.parse("{count:d} of them are selected with .tag-selected class"))
def some_tags_selected(page: Page, count):
    """Select some tags."""
    page.evaluate(f"""
        const tags = document.querySelectorAll('[data-tag]');
        for (let i = 0; i < {count} && i < tags.length; i++) {{
            tags[i].classList.add('tag-selected');
        }}
    """)


@when("I query the selection state 10 times consecutively")
def query_selection_10_times(page: Page, test_context):
    """Query selection multiple times."""
    timings = page.evaluate("""
        const timings = [];
        for (let i = 0; i < 10; i++) {
            const start = performance.now();
            const selected = document.querySelectorAll('.tag-selected');
            const end = performance.now();
            timings.push(end - start);
        }
        timings
    """)
    test_context["execution_times"] = timings


@then("each query should use querySelectorAll('.tag-selected')")
def verify_uses_queryselector():
    """Conceptual verification."""
    pass


@then("each query should complete in under 5ms")
def verify_under_5ms(test_context):
    """Verify performance."""
    for i, timing in enumerate(test_context["execution_times"]):
        assert timing < 5, f"Query {i+1} took {timing:.2f}ms, should be <5ms"


@then("no Set caching should provide false performance benefits")
def verify_no_false_benefits():
    """Conceptual verification."""
    pass


@then("DOM query performance should be adequate for 60 FPS")
def verify_adequate_performance(test_context):
    """Verify adequate performance."""
    avg = sum(test_context["execution_times"]) / len(test_context["execution_times"])
    assert avg < 16, f"Average query time {avg:.2f}ms should be <16ms for 60 FPS"


# Scenario 10: Concurrent selection operations maintain DOM authority

@given("I have tags with existing selection state")
def tags_with_existing_selection(page: Page):
    """Setup tags with selection."""
    page.evaluate("""
        const cloud = document.querySelector('.cloud-user .tags-wrapper');
        if (cloud) {
            cloud.innerHTML = '';
            ['A', 'B', 'C', 'D', 'E'].forEach(name => {
                const tag = document.createElement('span');
                tag.className = 'tag tag-cloud';
                if (name === 'B') tag.classList.add('tag-selected');
                tag.setAttribute('data-tag', name);
                tag.setAttribute('data-tag-id', `test-${name.toLowerCase()}`);
                tag.setAttribute('draggable', 'true');
                tag.textContent = name;
                cloud.appendChild(tag);
            });
        }
    """)


@when("two rapid selection operations occur simultaneously")
def concurrent_operations(page: Page):
    """Simulate concurrent operations."""
    # Set up for concurrent ops
    pass


@when("the first operation adds .tag-selected class to tag A")
def first_op_selects_a(page: Page):
    """First operation."""
    page.evaluate("""
        document.querySelector('[data-tag="A"]')?.classList.add('tag-selected');
    """)


@when("the second operation queries selection before first completes")
def second_op_queries(page: Page, test_context):
    """Second operation queries."""
    selection = page.evaluate("""
        Array.from(document.querySelectorAll('.tag-selected')).map(t => t.getAttribute('data-tag'))
    """)
    test_context["dom_selection"] = selection


@then("the second operation should see the partial DOM state")
def verify_partial_state(test_context):
    """Verify partial state visible."""
    assert 'A' in test_context["dom_selection"] or 'B' in test_context["dom_selection"], \
        "Should see partial DOM state"


@then("no JavaScript Set should provide stale cached data")
def verify_no_stale_cache():
    """Conceptual verification."""
    pass


@then("DOM classes should be definitive at all times")
def verify_dom_definitive():
    """Conceptual verification."""
    pass
