Feature: DATAOS Cache Violations - No State Caching Allowed
  As a system architect enforcing DATAOS principles
  I want to ensure deriveStateFromDOM never uses caching
  So that the DOM remains the single source of truth at all times

  Background:
    Given the drag-drop system is initialized
    And the DOM contains tag clouds and drop zones

  Scenario: deriveStateFromDOM never uses cache
    Given I have tags distributed across multiple zones
    When I call deriveStateFromDOM() the first time
    And I call deriveStateFromDOM() again immediately
    Then both calls should extract data fresh from the DOM
    And no cached state should be returned
    And the results should be identical but independently derived

  Scenario: Rapid successive calls return fresh DOM data
    Given I have a tag "Python" in the user cloud
    When I call deriveStateFromDOM() and capture the result
    And I move "Python" to the include zone in the DOM
    And I call deriveStateFromDOM() within 1 millisecond
    Then the second call should reflect the new DOM state
    And the first call result should differ from the second
    And no 1-second cache window should return stale data

  Scenario: DOM modifications immediately reflected in deriveStateFromDOM
    Given I have tags "JavaScript", "TypeScript", "Python" in various zones
    When I programmatically add a new tag "Rust" to the exclude zone
    And I call deriveStateFromDOM() within 1ms
    Then the state should include "Rust" in the exclude zone
    And the extraction should happen directly from the DOM
    And no cached state should miss the new tag

  Scenario: No stateCache variables exist in system
    Given the drag-drop system has been running for several operations
    When I inspect the SpatialDragDrop instance properties
    Then the stateCache property should not exist
    And the stateCacheTime property should not exist
    And the CACHE_DURATION constant should not exist
    And there should be no cache-related variables

  Scenario: Performance remains under 16ms without cache
    Given I have 100 tags distributed across all zones
    When I call deriveStateFromDOM() 10 times consecutively
    And I measure the execution time of each call
    Then each call should complete in under 16ms
    And the average execution time should be under 10ms
    And all calls should return fresh DOM data
    And removing the cache should not degrade performance

  Scenario: No invalidateCache method exists
    Given the drag-drop system is initialized
    When I inspect the SpatialDragDrop class prototype
    Then there should be no invalidateCache method
    And there should be no clearCache method
    And there should be no resetCache method
    And cache management methods should not exist

  Scenario: Concurrent state queries return independent fresh data
    Given I have tags in multiple zones with rapid operations occurring
    When I initiate two concurrent deriveStateFromDOM() calls
    And the DOM is modified between the calls
    Then each call should independently query the DOM
    And neither call should use cached data from the other
    And each call should reflect the DOM state at its execution time

  Scenario: Cache-related code removed from deriveStateFromDOM
    Given I inspect the deriveStateFromDOM method implementation
    When I examine the method's source code
    Then there should be no cache-checking logic
    And there should be no cache storage logic
    And there should be no Date.now() comparisons for cache expiry
    And the method should directly query the DOM and return

  Scenario: State extraction timing is deterministic
    Given I have a stable DOM with 50 tags across zones
    When I call deriveStateFromDOM() 100 times
    And I measure the execution time of each call
    Then the execution times should be consistent
    And there should be no cache-hit vs cache-miss timing variation
    And all calls should have similar DOM query performance
    And the timing should follow a normal distribution

  Scenario: Memory usage stable without cache objects
    Given the drag-drop system has processed 1000 operations
    When I check the memory footprint of the SpatialDragDrop instance
    Then there should be no stateCache object consuming memory
    And there should be no growing cache data structures
    And memory usage should be minimal and constant
    And garbage collection should handle all temporary state
