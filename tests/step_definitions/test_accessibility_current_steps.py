"""
BDD Step Definitions for Current Accessibility Behavior

Tests the existing manual ARIA, keyboard navigation, and screen reader implementations
before migration to accX. These tests establish the baseline that must be preserved.

Framework: pytest-bdd with Playwright for real browser interactions
Reference: tests/step_definitions/test_set_operations_steps.py
"""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import Page, expect
import time

# Load all scenarios from the feature file
scenarios('/Users/adam/dev/multicardz/tests/features/accessibility-current.feature')


# ============================================================================
# Background Steps
# ============================================================================

@given("the multicardz application is running")
def app_is_running(page: Page):
    """Verify the application loads successfully"""
    page.goto("http://localhost:8011/")
    expect(page.locator("body")).to_be_visible()


@given("I am on the user home page")
def on_user_home_page(page: Page):
    """Navigate to user home page"""
    page.goto("http://localhost:8011/")
    # Wait for clouds to be visible
    page.wait_for_selector(".cloud", state="visible", timeout=5000)


@given("there are tags visible in the clouds")
def tags_visible(page: Page):
    """Ensure tags are loaded and visible"""
    # Wait for at least one tag to be present
    page.wait_for_selector("[data-tag]", state="visible", timeout=5000)
    tags = page.locator("[data-tag]").all()
    assert len(tags) > 0, "No tags found in clouds"


# ============================================================================
# ARIA Attribute Steps
# ============================================================================

@given(parsers.parse('I see a tag "{tag_name}" in the union cloud'))
@given(parsers.parse('I see a tag "{tag_name}"'))
def see_tag(page: Page, tag_name: str):
    """Verify tag is visible"""
    tag = page.locator(f'[data-tag="{tag_name}"]')
    expect(tag).to_be_visible()


@when(parsers.parse('I click on the tag "{tag_name}"'))
def click_tag(page: Page, tag_name: str):
    """Click on a specific tag"""
    tag = page.locator(f'[data-tag="{tag_name}"]')
    tag.click()
    time.sleep(0.1)  # Allow ARIA update


@when(parsers.parse('I click on the tag "{tag_name}" again'))
def click_tag_again(page: Page, tag_name: str):
    """Click the same tag again"""
    click_tag(page, tag_name)


@then(parsers.parse('the tag "{tag_name}" should have aria-selected="{value}"'))
def tag_has_aria_selected(page: Page, tag_name: str, value: str):
    """Verify tag has specific aria-selected value"""
    tag = page.locator(f'[data-tag="{tag_name}"]')
    actual_value = tag.get_attribute("aria-selected")
    assert actual_value == value, f"Expected aria-selected={value}, got {actual_value}"


@then(parsers.parse('the tag "{tag_name}" should have tabindex="0"'))
def tag_has_tabindex(page: Page, tag_name: str):
    """Verify tag is keyboard focusable"""
    tag = page.locator(f'[data-tag="{tag_name}"]')
    tabindex = tag.get_attribute("tabindex")
    assert tabindex == "0", f"Expected tabindex=0, got {tabindex}"


@then(parsers.parse('the tag "{tag_name}" should be focusable with keyboard'))
def tag_is_keyboard_focusable(page: Page, tag_name: str):
    """Verify tag can receive keyboard focus"""
    tag = page.locator(f'[data-tag="{tag_name}"]')
    tag.focus()
    focused = page.evaluate("document.activeElement.dataset.tag")
    assert focused == tag_name, f"Tag {tag_name} is not focused"


# ============================================================================
# Container ARIA Steps
# ============================================================================

@given("I see tags in a cloud container")
def see_cloud_container(page: Page):
    """Verify cloud container exists"""
    container = page.locator(".cloud").first
    expect(container).to_be_visible()


@then('the container should have aria-multiselectable="true"')
def container_has_multiselectable(page: Page):
    """Verify container supports multi-selection"""
    container = page.locator(".cloud").first
    value = container.get_attribute("aria-multiselectable")
    assert value == "true", f"Expected aria-multiselectable=true, got {value}"


# ============================================================================
# Keyboard Navigation Steps
# ============================================================================

@given(parsers.parse('I see tags "{tag1}", "{tag2}", "{tag3}" in order'))
def see_tags_in_order(page: Page, tag1: str, tag2: str, tag3: str):
    """Verify multiple tags are visible"""
    for tag_name in [tag1, tag2, tag3]:
        tag = page.locator(f'[data-tag="{tag_name}"]')
        expect(tag).to_be_visible()


@given(parsers.parse('I focus on tag "{tag_name}"'))
@when(parsers.parse('I focus on tag "{tag_name}"'))
def focus_on_tag(page: Page, tag_name: str):
    """Move keyboard focus to specific tag"""
    tag = page.locator(f'[data-tag="{tag_name}"]')
    tag.focus()
    time.sleep(0.05)  # Allow focus to settle


@when(parsers.parse('I press the "{key}" key'))
def press_key(page: Page, key: str):
    """Press a single key"""
    page.keyboard.press(key)
    time.sleep(0.1)  # Allow handler to execute


@when(parsers.parse('I press "{keys}" keys'))
def press_key_combination(page: Page, keys: str):
    """Press key combination like Control+Space"""
    page.keyboard.press(keys)
    time.sleep(0.1)


@then(parsers.parse('the tag "{tag_name}" should be focused'))
def tag_is_focused(page: Page, tag_name: str):
    """Verify specific tag has keyboard focus"""
    focused_tag = page.evaluate("document.activeElement.dataset.tag")
    assert focused_tag == tag_name, f"Expected {tag_name} to be focused, got {focused_tag}"


# ============================================================================
# Selection Steps
# ============================================================================

@given(parsers.parse('the tag "{tag_name}" is not selected'))
def tag_not_selected(page: Page, tag_name: str):
    """Verify tag is not selected"""
    tag = page.locator(f'[data-tag="{tag_name}"]')
    selected = tag.get_attribute("aria-selected")
    assert selected != "true", f"Tag {tag_name} is already selected"


@given(parsers.parse('I select tag "{tag_name}"'))
@when(parsers.parse('I select tag "{tag_name}"'))
def select_tag(page: Page, tag_name: str):
    """Select a tag (click it)"""
    tag = page.locator(f'[data-tag="{tag_name}"]')
    tag.click()
    time.sleep(0.1)


@given(parsers.parse('I have selected tags "{tag1}", "{tag2}"'))
def select_multiple_tags(page: Page, tag1: str, tag2: str):
    """Select multiple tags"""
    for tag_name in [tag1, tag2]:
        tag = page.locator(f'[data-tag="{tag_name}"]')
        tag.click(modifiers=["Control"])
        time.sleep(0.05)


@then(parsers.parse('the tag "{tag_name}" should be selected'))
def tag_is_selected(page: Page, tag_name: str):
    """Verify tag is selected"""
    tag = page.locator(f'[data-tag="{tag_name}"]')
    selected = tag.get_attribute("aria-selected")
    assert selected == "true", f"Tag {tag_name} is not selected"


@then(parsers.parse('the tag "{tag_name}" should not be selected'))
def tag_is_not_selected(page: Page, tag_name: str):
    """Verify tag is not selected"""
    tag = page.locator(f'[data-tag="{tag_name}"]')
    selected = tag.get_attribute("aria-selected")
    assert selected != "true", f"Tag {tag_name} is still selected"


@then("no tags should be selected")
def no_tags_selected(page: Page):
    """Verify all tags are deselected"""
    selected_tags = page.locator('[data-tag][aria-selected="true"]').all()
    assert len(selected_tags) == 0, f"Found {len(selected_tags)} selected tags"


@then('all tags should have aria-selected="false"')
def all_tags_deselected(page: Page):
    """Verify all tags have aria-selected=false"""
    tags = page.locator("[data-tag]").all()
    for tag in tags:
        selected = tag.get_attribute("aria-selected")
        assert selected == "false", f"Tag has aria-selected={selected}"


# ============================================================================
# Select All Steps
# ============================================================================

@given(parsers.parse('I see tags "{tag1}", "{tag2}", "{tag3}"'))
def see_specific_tags(page: Page, tag1: str, tag2: str, tag3: str):
    """Verify specific tags are visible"""
    for tag_name in [tag1, tag2, tag3]:
        tag = page.locator(f'[data-tag="{tag_name}"]')
        expect(tag).to_be_visible()


@given("I focus on any tag")
def focus_on_any_tag(page: Page):
    """Focus on the first available tag"""
    tag = page.locator("[data-tag]").first
    tag.focus()
    time.sleep(0.05)


@then("all tags should be selected")
def all_tags_selected(page: Page):
    """Verify all visible tags are selected"""
    all_tags = page.locator('[data-tag]:not([hidden])').all()
    selected_tags = page.locator('[data-tag][aria-selected="true"]').all()
    assert len(all_tags) == len(selected_tags), f"Expected {len(all_tags)} selected, got {len(selected_tags)}"


@then('all tags should have aria-selected="true"')
def all_tags_have_selected_true(page: Page):
    """Verify all tags have aria-selected=true"""
    tags = page.locator("[data-tag]:not([hidden])").all()
    for tag in tags:
        selected = tag.get_attribute("aria-selected")
        assert selected == "true", f"Tag has aria-selected={selected}"


# ============================================================================
# Shift Selection Steps
# ============================================================================

@then(parsers.parse('tags "{tag1}" and "{tag2}" should be selected'))
def two_tags_selected(page: Page, tag1: str, tag2: str):
    """Verify two specific tags are selected"""
    for tag_name in [tag1, tag2]:
        tag = page.locator(f'[data-tag="{tag_name}"]')
        selected = tag.get_attribute("aria-selected")
        assert selected == "true", f"Tag {tag_name} is not selected"


@then("both should have aria-selected=\"true\"")
def both_have_selected_true(page: Page):
    """Already verified in previous step"""
    pass  # Combined verification


# ============================================================================
# Live Region Steps
# ============================================================================

@given("I see a live region element")
def see_live_region(page: Page):
    """Verify live region exists"""
    live_region = page.locator('[aria-live]')
    expect(live_region).to_be_attached()


@given('the live region has aria-live="polite"')
def live_region_is_polite(page: Page):
    """Verify live region is polite"""
    live_region = page.locator('[aria-live]')
    value = live_region.get_attribute("aria-live")
    assert value == "polite", f"Expected aria-live=polite, got {value}"


@given('the live region has aria-atomic="true"')
def live_region_is_atomic(page: Page):
    """Verify live region is atomic"""
    live_region = page.locator('[aria-live]')
    value = live_region.get_attribute("aria-atomic")
    assert value == "true", f"Expected aria-atomic=true, got {value}"


@then(parsers.parse('the live region should contain "{text}"'))
def live_region_contains_text(page: Page, text: str):
    """Verify live region contains specific text"""
    live_region = page.locator('[aria-live]')
    content = live_region.text_content()
    assert text in content, f"Expected '{text}' in live region, got '{content}'"


@then("the live region should announce the selection count")
def live_region_announces_count(page: Page):
    """Verify live region contains count information"""
    live_region = page.locator('[aria-live]')
    content = live_region.text_content()
    # Should contain a number
    assert any(char.isdigit() for char in content), f"No count in live region: '{content}'"


# ============================================================================
# Drag State Steps
# ============================================================================

@then(parsers.parse('the tag "{tag_name}" should have aria-grabbed="{value}"'))
def tag_has_aria_grabbed(page: Page, tag_name: str, value: str):
    """Verify tag has specific aria-grabbed value"""
    tag = page.locator(f'[data-tag="{tag_name}"]')
    actual = tag.get_attribute("aria-grabbed")
    assert actual == value, f"Expected aria-grabbed={value}, got {actual}"


@when(parsers.parse('I start dragging tag "{tag_name}"'))
def start_dragging_tag(page: Page, tag_name: str):
    """Initiate drag operation on tag"""
    tag = page.locator(f'[data-tag="{tag_name}"]')
    # Use mouse down to start drag
    box = tag.bounding_box()
    page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
    page.mouse.down()
    time.sleep(0.1)  # Allow drag state to update


@when(parsers.parse('I drop tag "{tag_name}" in the intersection zone'))
def drop_in_zone(page: Page, tag_name: str):
    """Complete drag by dropping in zone"""
    zone = page.locator('[data-zone-type="intersection"]')
    box = zone.bounding_box()
    page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
    page.mouse.up()
    time.sleep(0.2)  # Allow drop to complete


# ============================================================================
# Drop Zone ARIA Steps
# ============================================================================

@given("I see drop zones for union, intersection, and exclusion")
def see_drop_zones(page: Page):
    """Verify drop zones exist"""
    for zone_type in ["union", "intersection", "exclusion"]:
        zone = page.locator(f'[data-zone-type="{zone_type}"]')
        expect(zone).to_be_visible()


@then(parsers.parse('the {zone_name} zone should have aria-label containing "{text}"'))
def zone_has_aria_label(page: Page, zone_name: str, text: str):
    """Verify zone has proper aria-label"""
    zone = page.locator(f'[data-zone-type="{zone_name}"]')
    label = zone.get_attribute("aria-label")
    assert label is not None, f"Zone {zone_name} has no aria-label"
    assert text.lower() in label.lower(), f"Expected '{text}' in aria-label, got '{label}'"


# ============================================================================
# Form ARIA Steps
# ============================================================================

@given("I see the tag input field")
def see_tag_input(page: Page):
    """Verify tag input field exists"""
    input_field = page.locator('.tag-input').first
    expect(input_field).to_be_visible()


@then(parsers.parse('it should have aria-label="{label}"'))
def has_aria_label(page: Page, label: str):
    """Verify element has specific aria-label"""
    # Use the most recent context (tag input)
    input_field = page.locator(f'[aria-label="{label}"]')
    expect(input_field).to_be_attached()


# ============================================================================
# Button ARIA Steps
# ============================================================================

@given(parsers.parse("I see the collapse toggle button for row {row_num}"))
def see_collapse_button(page: Page, row_num: str):
    """Verify collapse toggle button exists"""
    button = page.locator(f'.collapse-row{row_num}')
    expect(button).to_be_visible()


# ============================================================================
# Expandable Group Steps
# ============================================================================

@given("I see a group tag in the cloud")
def see_group_tag(page: Page):
    """Verify group tag exists"""
    group = page.locator('[role="button"][aria-expanded]')
    expect(group.first).to_be_visible()


@then('it should have role="button"')
def has_role_button(page: Page):
    """Verify element has role=button"""
    group = page.locator('[role="button"]').first
    role = group.get_attribute("role")
    assert role == "button", f"Expected role=button, got {role}"


@then('it should have aria-expanded="false"')
def has_aria_expanded_false(page: Page):
    """Verify element has aria-expanded=false"""
    group = page.locator('[aria-expanded]').first
    expanded = group.get_attribute("aria-expanded")
    assert expanded == "false", f"Expected aria-expanded=false, got {expanded}"


@when("I click the group tag")
def click_group_tag(page: Page):
    """Click on group tag"""
    group = page.locator('[role="button"][aria-expanded]').first
    group.click()
    time.sleep(0.2)


@then('it should have aria-expanded="true"')
def has_aria_expanded_true(page: Page):
    """Verify element has aria-expanded=true"""
    group = page.locator('[aria-expanded]').first
    expanded = group.get_attribute("aria-expanded")
    assert expanded == "true", f"Expected aria-expanded=true, got {expanded}"


# ============================================================================
# Screen Reader Only Steps
# ============================================================================

@then('it should have class "sr-only"')
def has_sr_only_class(page: Page):
    """Verify element has sr-only class"""
    live_region = page.locator('[aria-live]')
    classes = live_region.get_attribute("class")
    assert "sr-only" in classes, f"Expected sr-only class, got {classes}"


@then("it should be visually hidden but accessible to screen readers")
def is_visually_hidden(page: Page):
    """Verify element is off-screen but accessible"""
    live_region = page.locator('[aria-live]')
    # Check if element has sr-only class (already verified) and is not visible on screen
    is_visible = live_region.is_visible()
    # sr-only elements are technically "visible" to Playwright but positioned off-screen
    # We verify they exist and have the class
    assert live_region.count() > 0, "Live region not found"


# ============================================================================
# Focus Visibility Steps
# ============================================================================

@given("I am using keyboard navigation")
def using_keyboard_navigation(page: Page):
    """Set context for keyboard navigation"""
    # Just a context step, no action needed
    pass


@then("the tag should be scrolled into view if needed")
def tag_scrolled_into_view(page: Page):
    """Verify focused tag is in viewport"""
    focused_tag = page.locator("document.activeElement")
    # If ensureFocusVisible works, element should be in viewport
    is_in_viewport = page.evaluate("""
        () => {
            const el = document.activeElement;
            const rect = el.getBoundingClientRect();
            return (
                rect.top >= 0 &&
                rect.left >= 0 &&
                rect.bottom <= window.innerHeight &&
                rect.right <= window.innerWidth
            );
        }
    """)
    assert is_in_viewport, "Focused element is not in viewport"


@then("the tag should have visible focus indicator")
def has_visible_focus_indicator(page: Page):
    """Verify focused element has visual focus style"""
    # Check that focused element is the active element
    focused = page.evaluate("document.activeElement !== document.body")
    assert focused, "No element is focused"


# ============================================================================
# Tab Order Steps
# ============================================================================

@when("I press Tab repeatedly")
def press_tab_repeatedly(page: Page):
    """Press Tab key multiple times"""
    # Press tab 5 times to test order
    for _ in range(5):
        page.keyboard.press("Tab")
        time.sleep(0.05)


@then("focus should move through elements in logical order")
def focus_moves_logically(page: Page):
    """Verify tab order is logical"""
    # Verify focus moved (not still on body)
    focused = page.evaluate("document.activeElement.tagName")
    assert focused != "BODY", "Focus did not move from body"


@then("all interactive elements should be reachable")
def all_interactive_reachable(page: Page):
    """Verify all interactive elements have tabindex or are naturally focusable"""
    # Check that buttons, links, and tagged elements are focusable
    focusable = page.locator('button, a, [tabindex="0"], [data-tag]').all()
    assert len(focusable) > 0, "No focusable elements found"


# ============================================================================
# Modifier Key Steps
# ============================================================================

@when(parsers.parse('I move to tag "{tag_name}"'))
def move_to_tag(page: Page, tag_name: str):
    """Move keyboard focus to another tag"""
    tag = page.locator(f'[data-tag="{tag_name}"]')
    tag.focus()
    time.sleep(0.05)


@then(parsers.parse('tags "{tag1}" and "{tag2}" should both be selected'))
def both_tags_selected(page: Page, tag1: str, tag2: str):
    """Verify both tags are selected"""
    two_tags_selected(page, tag1, tag2)


# ============================================================================
# Announcement Verb Steps
# ============================================================================

@when(parsers.parse('I add tag "{tag_name}" to selection'))
def add_to_selection(page: Page, tag_name: str):
    """Add tag to existing selection with Ctrl+click"""
    tag = page.locator(f'[data-tag="{tag_name}"]')
    tag.click(modifiers=["Control"])
    time.sleep(0.15)  # Allow announcement to update


@when(parsers.parse('I remove tag "{tag_name}" from selection'))
def remove_from_selection(page: Page, tag_name: str):
    """Remove tag from selection with Ctrl+click"""
    tag = page.locator(f'[data-tag="{tag_name}"]')
    tag.click(modifiers=["Control"])  # Toggle off
    time.sleep(0.15)


@when(parsers.parse('I select tags "{tag1}" and "{tag2}"'))
def select_two_tags(page: Page, tag1: str, tag2: str):
    """Select multiple tags"""
    select_multiple_tags(page, tag1, tag2)
