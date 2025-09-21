Feature: Set Theory Operations with Performance Optimization
  As a system processing large card collections
  I want mathematically rigorous set operations
  So that filtering achieves 26x performance improvement over existing solutions

  Scenario: Intersection filtering with mathematical precision
    Given I have 100,000 cards with various tag combinations
    When I filter by tag intersection using frozenset operations
    Then the result should be mathematically equivalent to set intersection
    And the operation should complete in <0.38ms per 1,000 cards

  Scenario: Union operations preserving card multiplicity
    Given I have card sets from different sources
    When I combine sets using union operations
    Then the result should include all cards from both sets
    And card instances should maintain identity through operations

  Scenario: Complex set operations with commutative properties
    Given I have multiple tag sets for filtering
    When I combine operations (A ∩ B) ∪ (C - D)
    Then the results should follow mathematical set theory laws
    And operations should be commutative where appropriate

  Scenario: Performance scaling with large datasets
    Given I have datasets ranging from 1K to 500K cards
    When I perform set operations on each dataset size
    Then performance should scale linearly with optimization
    And memory usage should remain within efficiency targets

  Scenario: Cache optimization for repeated operations
    Given I perform the same set operations multiple times
    When I measure performance on subsequent operations
    Then cache optimization should improve performance >70%
    And cache hits should be tracked for monitoring