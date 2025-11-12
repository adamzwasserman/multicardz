Feature: Current Accessibility Implementation
  As a multicardz user with accessibility needs
  I want all interactive elements to have proper ARIA attributes and keyboard navigation
  So that I can use the application with assistive technologies

  Background:
    Given the multicardz application is running
    And I am on the user home page
    And there are tags visible in the clouds

  Scenario: Tags have proper ARIA selection state
    Given I see a tag "union1" in the union cloud
    When I click on the tag "union1"
    Then the tag "union1" should have aria-selected="true"
    When I click on the tag "union1" again
    Then the tag "union1" should have aria-selected="false"

  Scenario: Tags are keyboard focusable
    Given I see a tag "union1" in the union cloud
    Then the tag "union1" should have tabindex="0"
    And the tag "union1" should be focusable with keyboard

  Scenario: Multi-selection container has ARIA attribute
    Given I see tags in a cloud container
    Then the container should have aria-multiselectable="true"

  Scenario: Arrow key navigation moves focus between tags
    Given I see tags "union1", "union2", "union3" in order
    And I focus on tag "union1"
    When I press the "ArrowRight" key
    Then the tag "union2" should be focused
    When I press the "ArrowDown" key
    Then the tag "union3" should be focused
    When I press the "ArrowLeft" key
    Then the tag "union2" should be focused
    When I press the "ArrowUp" key
    Then the tag "union1" should be focused

  Scenario: Space key toggles tag selection
    Given I focus on tag "union1"
    And the tag "union1" is not selected
    When I press the "Space" key
    Then the tag "union1" should be selected
    And the tag "union1" should have aria-selected="true"
    When I press "Control+Space" keys
    Then the tag "union1" should not be selected
    And the tag "union1" should have aria-selected="false"

  Scenario: Enter key selects tag
    Given I focus on tag "union1"
    And the tag "union1" is not selected
    When I press the "Enter" key
    Then the tag "union1" should be selected
    And the tag "union1" should have aria-selected="true"

  Scenario: Escape key clears selection
    Given I have selected tags "union1", "union2"
    When I press the "Escape" key
    Then no tags should be selected
    And all tags should have aria-selected="false"

  Scenario: Ctrl+A selects all tags
    Given I see tags "union1", "union2", "union3"
    And I focus on any tag
    When I press "Control+a" keys
    Then all tags should be selected
    And all tags should have aria-selected="true"

  Scenario: Shift+Arrow extends selection
    Given I focus on tag "union1"
    And I select tag "union1"
    When I press "Shift+ArrowRight" keys
    Then tags "union1" and "union2" should be selected
    And both should have aria-selected="true"

  Scenario: Live region announces selection changes
    Given I see a live region element
    And the live region has aria-live="polite"
    And the live region has aria-atomic="true"
    When I select tag "union1"
    Then the live region should contain "union1 selected"

  Scenario: Live region announces multiple selections
    Given I see a live region element
    When I select tags "union1" and "union2"
    Then the live region should announce the selection count

  Scenario: Drag state is announced with aria-grabbed
    Given I see a tag "union1"
    Then the tag "union1" should have aria-grabbed="false"
    When I start dragging tag "union1"
    Then the tag "union1" should have aria-grabbed="true"
    When I drop tag "union1" in the intersection zone
    Then the tag "union1" should have aria-grabbed="false"

  Scenario: Drop zones have aria-label
    Given I see drop zones for union, intersection, and exclusion
    Then the union zone should have aria-label containing "union"
    And the intersection zone should have aria-label containing "intersection"
    And the exclusion zone should have aria-label containing "exclusion"

  Scenario: Form inputs have aria-label
    Given I see the tag input field
    Then it should have aria-label="add user tag"

  Scenario: Buttons have aria-label for screen readers
    Given I see the collapse toggle button for row 1
    Then it should have aria-label="Toggle row 1"

  Scenario: Expandable groups have aria-expanded
    Given I see a group tag in the cloud
    Then it should have role="button"
    And it should have aria-expanded="false"
    When I click the group tag
    Then it should have aria-expanded="true"

  Scenario: Screen reader only content is visually hidden
    Given I see a live region element
    Then it should have class "sr-only"
    And it should be visually hidden but accessible to screen readers

  Scenario: Focus is visible when navigating with keyboard
    Given I am using keyboard navigation
    When I focus on tag "union1"
    Then the tag should be scrolled into view if needed
    And the tag should have visible focus indicator

  Scenario: Tab order is logical
    Given I am on the user home page
    When I press Tab repeatedly
    Then focus should move through elements in logical order
    And all interactive elements should be reachable

  Scenario: Keyboard navigation respects modifiers
    Given I focus on tag "union1"
    When I press "Shift+Space" keys
    And I move to tag "union2"
    And I press "Shift+Space" keys
    Then tags "union1" and "union2" should both be selected

  Scenario: Selection announcement uses proper verbs
    Given I see a live region element
    When I add tag "union1" to selection
    Then the live region should contain "added to selection"
    When I remove tag "union1" from selection
    Then the live region should contain "removed from selection"
