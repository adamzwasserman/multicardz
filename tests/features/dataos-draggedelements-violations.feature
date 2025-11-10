Feature: DATAOS draggedElements Violations - No Duplicate State in JavaScript Array
  As a system architect enforcing DATAOS principles
  I want to ensure dragged element state is derived from DOM .dragging class only
  So that no duplicate state exists in JavaScript array variables

  Background:
    Given the drag-drop system is initialized
    And the DOM contains draggable tags

  Scenario: No draggedElements array exists in JavaScript
    Given the drag-drop system has been running
    When I inspect the SpatialDragDrop instance for draggedElements property
    Then the draggedElements array should not exist
    And there should be no JavaScript array variable for dragged state
    And dragged state should only exist in DOM .dragging class

  Scenario: Dragged elements identified by DOM dragging class
    Given I have 5 tags in the cloud
    When I start dragging tag "Python"
    And the system needs to identify what's being dragged
    Then it should query DOM for elements with .dragging class
    And no JavaScript array should store dragged element references
    And the .dragging class should be the authoritative source

  Scenario: Multi-drag operations use DOM not array
    Given I have tags "JavaScript", "Python", "Ruby" selected
    When I start dragging the selected tags
    Then each tag should get .dragging class added to DOM
    And no JavaScript array.push() operations should occur
    And querying dragged elements should use querySelectorAll('.dragging')
    And the array length should come from DOM query not variable

  Scenario: Drop operations clear DOM classes not array
    Given I am dragging 3 tags with .dragging class
    When I complete the drop operation
    Then all .dragging classes should be removed from DOM
    And no JavaScript array = [] assignment should occur
    And no array.length = 0 operation should occur
    And querying dragged elements should return empty from DOM

  Scenario: Concurrent drags maintain DOM consistency
    Given I have multiple tags that can be dragged
    When two drag operations are initiated rapidly
    Then each operation should add .dragging class to respective tags
    And no shared JavaScript array should cause conflicts
    And each drag should independently query DOM for .dragging elements
    And DOM classes should prevent state collision

  Scenario: Drag start adds DOM class not array entry
    Given I have tag "TypeScript" in the cloud
    When I mousedown on "TypeScript" to start drag
    Then "TypeScript" should get .dragging class in DOM
    And no draggedElements.push() should occur
    And the drag state should be readable from DOM class only

  Scenario: Drag cancellation removes DOM class not clears array
    Given I am dragging tags "Go" and "Rust"
    When I press ESC to cancel the drag
    Then both tags should lose .dragging class
    And no array.splice() or array = [] should occur
    And querying dragged elements should return empty

  Scenario: Ghost image generation queries DOM not array
    Given I am dragging multiple selected tags
    When the system generates the drag ghost image
    Then it should query document.querySelectorAll('.dragging')
    And it should not iterate over draggedElements array
    And the ghost should reflect current DOM state

  Scenario: No draggedElements property in constructor
    Given I inspect the drag-drop source code
    When I examine the SpatialDragDrop constructor
    Then there should be no this.draggedElements = [] initialization
    And no array variable should be created for dragged state
    And constructor should not setup drag state variables

  Scenario: Performance adequate without array caching
    Given I have 50 tags in the cloud
    When I drag 10 selected tags
    And the system queries dragged elements 5 times during drag
    Then each query should complete in under 3ms
    And DOM query performance should be adequate
    And no array caching should provide false benefits
