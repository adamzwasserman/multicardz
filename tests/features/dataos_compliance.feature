Feature: DATAOS Compliance - DOM as Single Source of Truth
  As a system architect
  I want to ensure the drag-drop system maintains DOM as the only source of truth
  So that state never diverges and rapid operations maintain perfect consistency

  Background:
    Given the drag-drop system is initialized
    And the DOM contains tag clouds and drop zones

  Scenario: deriveStateFromDOM returns fresh data on every call
    Given I have tags in multiple zones
    When I call deriveStateFromDOM() twice in rapid succession
    Then both calls should return identical fresh data from the DOM
    And no cached data should be returned
    And the execution time should be under 16ms for 60 FPS compliance

  Scenario: No state cache exists after operations
    Given I have performed multiple drag-drop operations
    When I inspect the SpatialDragDrop instance
    Then the stateCache property should be null or undefined
    And the stateCacheTime property should be 0 or undefined
    And the CACHE_DURATION constant should not exist

  Scenario: Rapid tag movements maintain consistency
    Given I have a tag "JavaScript" in the user cloud
    When I drag "JavaScript" to the "include" zone
    And I immediately query the system state
    Then the state should reflect "JavaScript" in the "include" zone
    And the tag should have moved in the DOM
    And there should be no divergence between DOM and JavaScript state

  Scenario: State extraction within 1ms after DOM mutation
    Given I have multiple tags in various zones
    When I programmatically move a tag in the DOM
    And I call deriveStateFromDOM() within 1ms
    Then the state should reflect the new DOM position immediately
    And no 1-second cache window should cause stale data

  Scenario: selectedTags derived from DOM not JavaScript Set
    Given I have selected 5 tags using Ctrl+click
    When I query the selection state
    Then the selection should be read from DOM .tag-selected classes
    And no JavaScript Set variable should exist for selection
    And adding .tag-selected class should be the only selection mechanism

  Scenario: draggedElements derived from DOM not JavaScript array
    Given I start dragging 3 selected tags
    When the system needs to know what's being dragged
    Then it should query DOM for .dragging classes
    And no JavaScript array should store dragged element references
    And the DOM .dragging class should be the authoritative source

  Scenario: No selectionState object exists
    Given the drag-drop system is running
    When I inspect the SpatialDragDrop instance
    Then there should be no selectionState object
    And no selectedTags Set should exist
    And no anchorTag cached reference should exist
    And no lastSelectedTag cached reference should exist
    And all selection state should come from DOM queries

  Scenario: Ghost image canvas cleanup doesn't cache state
    Given I have dragged multiple tags creating a ghost image
    When the drag operation completes
    Then the ghost canvas should be cleaned up and removed
    And no currentGhostCanvas reference should remain
    And no currentGhostImage reference should remain
    And the cleanup should be immediate, not cached

  Scenario: Concurrent operations maintain DOM authority
    Given I have two rapid operations happening simultaneously
    When the first operation modifies the DOM
    And the second operation queries state before first completes
    Then the second operation should see the partial DOM state
    And there should be no cached state causing incorrect behavior
    And the DOM should be the definitive source at all times

  Scenario: Performance maintained without caching
    Given I have 1000 tags across multiple zones
    When I call deriveStateFromDOM() 10 times in sequence
    Then each call should complete in under 10ms
    And all 10 calls should return identical fresh data
    And no performance degradation should occur from cache removal
    And DOM queries should be optimized with efficient selectors

  Scenario: No invalidateCache method exists
    Given the drag-drop system is initialized
    When I inspect the SpatialDragDrop prototype
    Then there should be no invalidateCache method
    And no cache management methods should exist
    And all state access should be direct DOM queries

  Scenario: State consistency during rapid multi-selection
    Given I have 20 tags visible in the cloud
    When I rapidly Shift+click through 10 tags in 100ms
    Then each click should update DOM .tag-selected classes immediately
    And querying selection after each click should show current state
    And no JavaScript-side selection tracking should cause lag
    And the final selection should match exactly what's in the DOM
