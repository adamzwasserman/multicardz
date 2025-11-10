Feature: DATAOS selectedTags Violations - No Duplicate State in JavaScript
  As a system architect enforcing DATAOS principles
  I want to ensure selection state is derived from DOM classes only
  So that no duplicate state exists in JavaScript Set variables

  Background:
    Given the drag-drop system is initialized
    And the DOM contains selectable tags

  Scenario: No selectedTags Set exists in JavaScript
    Given the drag-drop system has been running
    When I inspect the SpatialDragDrop instance for selectedTags property
    Then the selectedTags Set should not exist
    And there should be no JavaScript Set variable for selection
    And selection state should only exist in DOM classes

  Scenario: Selection state derived from DOM classes only
    Given I have 5 tags visible in the tag cloud
    When I select 3 tags by adding .tag-selected class
    And I query the selection state
    Then the system should read selection from DOM .tag-selected classes
    And no JavaScript Set should store selected tag references
    And the DOM classes should be the authoritative source

  Scenario: Multi-select operations use DOM not Set
    Given I have 10 tags in the cloud
    When I Ctrl+click on tag 1 to select it
    And I Ctrl+click on tag 3 to select it
    And I Ctrl+click on tag 5 to select it
    Then each selection should add .tag-selected class to the DOM
    And no JavaScript Set.add() operations should occur
    And querying selection should use querySelectorAll not Set iteration

  Scenario: Clearing selection removes DOM classes not Set entries
    Given I have 5 tags selected with .tag-selected class
    When I click outside the tag area to clear selection
    Then all .tag-selected classes should be removed from DOM
    And no JavaScript Set.clear() operation should occur
    And querying selection should return empty from DOM query

  Scenario: Rapid selection changes maintain DOM consistency
    Given I have 20 tags in the cloud
    When I rapidly Shift+click through 10 tags in 100ms
    Then each click should update DOM .tag-selected classes immediately
    And no JavaScript Set should track selection state
    And querying selection after each click should match DOM exactly
    And there should be no lag from JavaScript-side Set operations

  Scenario: Selection toggle uses DOM class manipulation only
    Given I have tag "Python" selected with .tag-selected class
    When I Ctrl+click on "Python" to deselect it
    Then the .tag-selected class should be removed from DOM
    And no JavaScript Set.delete() operation should occur
    And querying selection should not include "Python"
    And the DOM should be the single source of truth

  Scenario: Shift-selection range uses DOM query not Set
    Given I have tags numbered 1 through 10 in the cloud
    And tag 3 is selected as the anchor
    When I Shift+click on tag 7
    Then tags 3, 4, 5, 6, 7 should have .tag-selected class
    And the range should be calculated from DOM state not Set
    And no Set operations should be used for range selection

  Scenario: No selectionState object exists
    Given the drag-drop system is initialized
    When I inspect the SpatialDragDrop instance
    Then there should be no selectionState object
    And there should be no selectedTags Set property
    And there should be no anchorTag cached reference
    And there should be no lastSelectedTag cached reference
    And all selection state should come from DOM queries

  Scenario: Selection query performance without Set caching
    Given I have 100 tags in the cloud
    And 50 of them are selected with .tag-selected class
    When I query the selection state 10 times consecutively
    Then each query should use querySelectorAll('.tag-selected')
    And each query should complete in under 5ms
    And no Set caching should provide false performance benefits
    And DOM query performance should be adequate for 60 FPS

  Scenario: Concurrent selection operations maintain DOM authority
    Given I have tags with existing selection state
    When two rapid selection operations occur simultaneously
    And the first operation adds .tag-selected class to tag A
    And the second operation queries selection before first completes
    Then the second operation should see the partial DOM state
    And no JavaScript Set should provide stale cached data
    And DOM classes should be definitive at all times
