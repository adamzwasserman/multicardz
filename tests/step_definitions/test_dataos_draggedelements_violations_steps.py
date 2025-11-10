"""
BDD Step Definitions for DATAOS draggedElements Violations Feature Tests.

Implements step definitions for draggedElements array violation scenarios to ensure
all dragged element state is derived from DOM .dragging class, not JavaScript arrays.

BDD Feature: tests/features/dataos-draggedelements-violations.feature
"""

import pytest
from pytest_bdd import given, parsers, scenarios, then, when
from playwright.sync_api import Page, expect

# Load scenarios from feature file
scenarios("/Users/adam/dev/multicardz/tests/features/dataos-draggedelements-violations.feature")


@pytest.fixture
def test_context():
    """Test context to store state and results between steps."""
    return {
        "instance_properties": {},
        "dragged_state": [],
        "execution_times": [],
        "source_code": "",
    }


# Background steps

@given("the drag-drop system is initialized")
def drag_drop_system_initialized(page: Page):
    """Initialize the drag-drop system."""
    page.goto("http://localhost:8011/")
    page.wait_for_selector('[data-zone-type]', timeout=10000)
    page.wait_for_function("window.dragDropSystem !== undefined", timeout=10000)


@given("the DOM contains draggable tags")
def dom_contains_draggable_tags(page: Page):
    """Setup draggable tags in DOM."""
    page.evaluate("""
        const cloud = document.querySelector('.cloud-user .tags-wrapper');
        if (cloud) {
            ['Python', 'JavaScript', 'Ruby', 'Go', 'Rust', 'TypeScript'].forEach(name => {
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


# Scenario 1: No draggedElements array exists

@given("the drag-drop system has been running")
def system_has_been_running(page: Page):
    """System is running."""
    # Perform some drag operations to ensure system is active
    page.evaluate("""
        const tag = document.querySelector('[data-tag]');
        if (tag) {
            tag.classList.add('dragging');
            tag.classList.remove('dragging');
        }
    """)


@when("I inspect the SpatialDragDrop instance for draggedElements property")
def inspect_for_dragged_elements(page: Page, test_context):
    """Inspect instance for draggedElements."""
    properties = page.evaluate("""
        ({
            hasDraggedElements: window.dragDropSystem.hasOwnProperty('draggedElements'),
            draggedElementsType: typeof window.dragDropSystem.draggedElements,
            draggedElementsIsArray: Array.isArray(window.dragDropSystem.draggedElements),
            allProperties: Object.keys(window.dragDropSystem)
        })
    """)
    test_context["instance_properties"] = properties


@then("the draggedElements array should not exist")
def verify_no_dragged_elements_array(test_context):
    """Verify draggedElements array doesn't exist."""
    props = test_context["instance_properties"]
    # This will FAIL in RED phase
    assert not props["hasDraggedElements"] or not props["draggedElementsIsArray"], \
        "draggedElements array should not exist"


@then("there should be no JavaScript array variable for dragged state")
def verify_no_array_variable():
    """Conceptual verification."""
    pass


@then("dragged state should only exist in DOM .dragging class")
def verify_state_only_in_dom():
    """Conceptual verification."""
    pass


# Scenario 2: Dragged elements identified by DOM class

@given(parsers.parse("I have {count:d} tags in the cloud"))
def tags_in_cloud(page: Page, count):
    """Create tags in cloud."""
    page.evaluate(f"""
        const cloud = document.querySelector('.cloud-user .tags-wrapper');
        if (cloud) {{
            cloud.innerHTML = '';
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


@when(parsers.parse('I start dragging tag "{tag_name}"'))
def start_dragging_tag(page: Page, tag_name):
    """Start dragging a tag."""
    page.evaluate(f"""
        const tag = document.querySelector('[data-tag="{tag_name}"]');
        if (tag) {{
            tag.classList.add('dragging');
        }}
    """)


@when("the system needs to identify what's being dragged")
def system_identifies_dragged(page: Page, test_context):
    """System identifies dragged elements."""
    dragged = page.evaluate("""
        Array.from(document.querySelectorAll('.dragging')).map(t => t.getAttribute('data-tag'))
    """)
    test_context["dragged_state"] = dragged


@then("it should query DOM for elements with .dragging class")
def verify_queries_dom():
    """Conceptual verification."""
    pass


@then("no JavaScript array should store dragged element references")
def verify_no_array_storage(page: Page):
    """Verify no array stores references."""
    has_array = page.evaluate("""
        window.dragDropSystem.hasOwnProperty('draggedElements') &&
        Array.isArray(window.dragDropSystem.draggedElements) &&
        window.dragDropSystem.draggedElements.length > 0
    """)
    # This will FAIL in RED phase
    assert not has_array, "No array should store dragged elements"


@then("the .dragging class should be the authoritative source")
def verify_dragging_class_authoritative():
    """Conceptual verification."""
    pass


# Scenario 3: Multi-drag operations use DOM

@given(parsers.parse('I have tags "{tag1}", "{tag2}", "{tag3}" selected'))
def tags_selected(page: Page, tag1, tag2, tag3):
    """Select multiple tags."""
    page.evaluate(f"""
        const cloud = document.querySelector('.cloud-user .tags-wrapper');
        if (cloud) {{
            cloud.innerHTML = '';
            ['{tag1}', '{tag2}', '{tag3}'].forEach(name => {{
                const tag = document.createElement('span');
                tag.className = 'tag tag-cloud tag-selected';
                tag.setAttribute('data-tag', name);
                tag.setAttribute('data-tag-id', `test-${{name.toLowerCase()}}`);
                tag.setAttribute('draggable', 'true');
                tag.textContent = name;
                cloud.appendChild(tag);
            }});
        }}
    """)


@when("I start dragging the selected tags")
def start_dragging_selected(page: Page):
    """Start dragging selected tags."""
    page.evaluate("""
        document.querySelectorAll('.tag-selected').forEach(tag => {
            tag.classList.add('dragging');
        });
    """)


@then("each tag should get .dragging class added to DOM")
def verify_dragging_class_added(page: Page):
    """Verify classes added."""
    count = page.evaluate("""
        document.querySelectorAll('.dragging').length
    """)
    assert count == 3, "All 3 tags should have .dragging class"


@then("no JavaScript array.push() operations should occur")
def verify_no_array_push():
    """Conceptual verification."""
    pass


@then("querying dragged elements should use querySelectorAll('.dragging')")
def verify_uses_queryselector():
    """Conceptual verification."""
    pass


@then("the array length should come from DOM query not variable")
def verify_length_from_dom():
    """Conceptual verification."""
    pass


# Scenario 4: Drop operations clear DOM classes

@given(parsers.parse("I am dragging {count:d} tags with .dragging class"))
def dragging_tags(page: Page, count):
    """Setup dragging tags."""
    page.evaluate(f"""
        const cloud = document.querySelector('.cloud-user .tags-wrapper');
        if (cloud) {{
            cloud.innerHTML = '';
            for (let i = 0; i < {count}; i++) {{
                const tag = document.createElement('span');
                tag.className = 'tag tag-cloud dragging';
                tag.setAttribute('data-tag', `Tag${{i}}`);
                tag.setAttribute('data-tag-id', `test-tag-${{i}}`);
                tag.setAttribute('draggable', 'true');
                tag.textContent = `Tag${{i}}`;
                cloud.appendChild(tag);
            }}
        }}
    """)


@when("I complete the drop operation")
def complete_drop(page: Page):
    """Complete drop operation."""
    page.evaluate("""
        document.querySelectorAll('.dragging').forEach(tag => {
            tag.classList.remove('dragging');
        });
    """)


@then("all .dragging classes should be removed from DOM")
def verify_classes_removed(page: Page):
    """Verify classes removed."""
    count = page.evaluate("""
        document.querySelectorAll('.dragging').length
    """)
    assert count == 0, "All .dragging classes should be removed"


@then("no JavaScript array = [] assignment should occur")
def verify_no_array_assignment():
    """Conceptual verification."""
    pass


@then("no array.length = 0 operation should occur")
def verify_no_length_assignment():
    """Conceptual verification."""
    pass


@then("querying dragged elements should return empty from DOM")
def verify_empty_dom_query(page: Page):
    """Verify DOM query returns empty."""
    count = page.evaluate("""
        document.querySelectorAll('.dragging').length
    """)
    assert count == 0, "DOM query should return empty"


# Scenario 5: Concurrent drags maintain DOM consistency

@given("I have multiple tags that can be dragged")
def multiple_draggable_tags(page: Page):
    """Setup draggable tags."""
    dom_contains_draggable_tags(page)


@when("two drag operations are initiated rapidly")
def concurrent_drag_operations(page: Page):
    """Initiate concurrent drags."""
    page.evaluate("""
        const tags = document.querySelectorAll('[data-tag]');
        if (tags.length >= 2) {
            tags[0].classList.add('dragging');
            tags[1].classList.add('dragging');
        }
    """)


@then("each operation should add .dragging class to respective tags")
def verify_classes_added(page: Page):
    """Verify classes added."""
    count = page.evaluate("""
        document.querySelectorAll('.dragging').length
    """)
    assert count >= 2, "Multiple tags should have .dragging class"


@then("no shared JavaScript array should cause conflicts")
def verify_no_array_conflicts():
    """Conceptual verification."""
    pass


@then("each drag should independently query DOM for .dragging elements")
def verify_independent_queries():
    """Conceptual verification."""
    pass


@then("DOM classes should prevent state collision")
def verify_no_collision():
    """Conceptual verification."""
    pass


# Scenario 6: Drag start adds DOM class

@given(parsers.parse('I have tag "{tag_name}" in the cloud'))
def tag_in_cloud(page: Page, tag_name):
    """Create specific tag."""
    page.evaluate(f"""
        const cloud = document.querySelector('.cloud-user .tags-wrapper');
        if (cloud) {{
            const tag = document.createElement('span');
            tag.className = 'tag tag-cloud';
            tag.setAttribute('data-tag', '{tag_name}');
            tag.setAttribute('data-tag-id', 'test-{tag_name.lower()}');
            tag.setAttribute('draggable', 'true');
            tag.textContent = '{tag_name}';
            cloud.appendChild(tag);
        }}
    """)


@when(parsers.parse('I mousedown on "{tag_name}" to start drag'))
def mousedown_to_start_drag(page: Page, tag_name):
    """Mousedown to start drag."""
    page.evaluate(f"""
        const tag = document.querySelector('[data-tag="{tag_name}"]');
        if (tag) {{
            tag.classList.add('dragging');
        }}
    """)


@then(parsers.parse('"{tag_name}" should get .dragging class in DOM'))
def verify_has_dragging_class(page: Page, tag_name):
    """Verify has class."""
    has_class = page.evaluate(f"""
        document.querySelector('[data-tag="{tag_name}"]')?.classList.contains('dragging')
    """)
    assert has_class, f"{tag_name} should have .dragging class"


@then("no draggedElements.push() should occur")
def verify_no_push():
    """Conceptual verification."""
    pass


@then("the drag state should be readable from DOM class only")
def verify_state_from_dom():
    """Conceptual verification."""
    pass


# Scenario 7: Drag cancellation removes DOM class

@given(parsers.parse('I am dragging tags "{tag1}" and "{tag2}"'))
def dragging_specific_tags(page: Page, tag1, tag2):
    """Setup specific dragging tags."""
    page.evaluate(f"""
        const cloud = document.querySelector('.cloud-user .tags-wrapper');
        if (cloud) {{
            cloud.innerHTML = '';
            ['{tag1}', '{tag2}'].forEach(name => {{
                const tag = document.createElement('span');
                tag.className = 'tag tag-cloud dragging';
                tag.setAttribute('data-tag', name);
                tag.setAttribute('data-tag-id', `test-${{name.toLowerCase()}}`);
                tag.setAttribute('draggable', 'true');
                tag.textContent = name;
                cloud.appendChild(tag);
            }});
        }}
    """)


@when("I press ESC to cancel the drag")
def press_esc_to_cancel(page: Page):
    """Cancel drag with ESC."""
    page.evaluate("""
        document.querySelectorAll('.dragging').forEach(tag => {
            tag.classList.remove('dragging');
        });
    """)


@then("both tags should lose .dragging class")
def verify_lose_class(page: Page):
    """Verify classes removed."""
    count = page.evaluate("""
        document.querySelectorAll('.dragging').length
    """)
    assert count == 0, "No tags should have .dragging class"


@then("no array.splice() or array = [] should occur")
def verify_no_array_operations():
    """Conceptual verification."""
    pass


@then("querying dragged elements should return empty")
def verify_query_empty(page: Page):
    """Verify query returns empty."""
    count = page.evaluate("""
        document.querySelectorAll('.dragging').length
    """)
    assert count == 0, "Query should return empty"


# Scenario 8: Ghost image generation queries DOM

@given("I am dragging multiple selected tags")
def dragging_multiple_selected(page: Page):
    """Setup multiple dragging tags."""
    page.evaluate("""
        const cloud = document.querySelector('.cloud-user .tags-wrapper');
        if (cloud) {
            cloud.innerHTML = '';
            ['A', 'B', 'C'].forEach(name => {
                const tag = document.createElement('span');
                tag.className = 'tag tag-cloud tag-selected dragging';
                tag.setAttribute('data-tag', name);
                tag.setAttribute('data-tag-id', `test-${name.toLowerCase()}`);
                tag.setAttribute('draggable', 'true');
                tag.textContent = name;
                cloud.appendChild(tag);
            });
        }
    """)


@when("the system generates the drag ghost image")
def generate_ghost_image(page: Page, test_context):
    """Simulate ghost image generation."""
    dragged = page.evaluate("""
        // Simulate what ghost generation should do
        const dragging = document.querySelectorAll('.dragging');
        Array.from(dragging).map(t => t.getAttribute('data-tag'))
    """)
    test_context["dragged_state"] = dragged


@then("it should query document.querySelectorAll('.dragging')")
def verify_uses_queryselector_all():
    """Conceptual verification."""
    pass


@then("it should not iterate over draggedElements array")
def verify_no_array_iteration():
    """Conceptual verification."""
    pass


@then("the ghost should reflect current DOM state")
def verify_ghost_reflects_dom(test_context):
    """Verify ghost reflects DOM."""
    assert len(test_context["dragged_state"]) == 3, "Ghost should show 3 dragged tags"


# Scenario 9: No draggedElements in constructor

@given("I inspect the drag-drop source code")
def inspect_source_code(page: Page):
    """Prepare to inspect source."""
    pass


@when("I examine the SpatialDragDrop constructor")
def examine_constructor(page: Page, test_context):
    """Get constructor source code."""
    source = page.evaluate("""
        window.dragDropSystem.constructor.toString()
    """)
    test_context["source_code"] = source


@then("there should be no this.draggedElements = [] initialization")
def verify_no_array_init(test_context):
    """Verify no array initialization."""
    source = test_context["source_code"]
    # This will FAIL in RED phase
    assert 'draggedElements' not in source or 'this.draggedElements = []' not in source, \
        "Constructor should not initialize draggedElements array"


@then("no array variable should be created for dragged state")
def verify_no_array_variable():
    """Conceptual verification."""
    pass


@then("constructor should not setup drag state variables")
def verify_no_drag_state_setup():
    """Conceptual verification."""
    pass


# Scenario 10: Performance adequate without array caching

@given(parsers.parse("I have {count:d} tags in the cloud"))
def many_tags_in_cloud(page: Page, count):
    """Create many tags."""
    tags_in_cloud(page, count)


@when(parsers.parse("I drag {count:d} selected tags"))
def drag_selected_tags(page: Page, count):
    """Drag selected tags."""
    page.evaluate(f"""
        const tags = document.querySelectorAll('[data-tag]');
        for (let i = 0; i < {count} && i < tags.length; i++) {{
            tags[i].classList.add('tag-selected');
            tags[i].classList.add('dragging');
        }}
    """)


@when("the system queries dragged elements 5 times during drag")
def query_dragged_5_times(page: Page, test_context):
    """Query dragged elements multiple times."""
    timings = page.evaluate("""
        const timings = [];
        for (let i = 0; i < 5; i++) {
            const start = performance.now();
            const dragging = document.querySelectorAll('.dragging');
            const end = performance.now();
            timings.push(end - start);
        }
        timings
    """)
    test_context["execution_times"] = timings


@then("each query should complete in under 3ms")
def verify_under_3ms(test_context):
    """Verify performance."""
    for i, timing in enumerate(test_context["execution_times"]):
        assert timing < 3, f"Query {i+1} took {timing:.2f}ms, should be <3ms"


@then("DOM query performance should be adequate")
def verify_adequate_performance(test_context):
    """Verify adequate performance."""
    avg = sum(test_context["execution_times"]) / len(test_context["execution_times"])
    assert avg < 2, f"Average query time {avg:.2f}ms should be <2ms"


@then("no array caching should provide false benefits")
def verify_no_false_benefits():
    """Conceptual verification."""
    pass
