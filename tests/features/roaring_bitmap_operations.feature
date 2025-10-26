# tests/features/roaring_bitmap_operations.feature
Feature: RoaringBitmap Set Operations
  As a system
  I want efficient set operations
  So that tag filtering is performant

  Scenario: Intersection of tag sets
    Given I have cards with multiple tags
    When I perform intersection operation
    Then only cards with ALL specified tags are returned
    And operation completes in under 50ms
    And result is a frozenset

  Scenario: Union of tag sets
    Given I have cards with various tags
    When I perform union operation
    Then cards with ANY specified tags are returned
    And duplicates are eliminated
    And result maintains immutability

  Scenario: Complex nested operations
    Given I have a complex filter expression
    When I combine intersection and union operations
    Then the result follows set theory rules
    And performance remains under threshold
    And operations use pure functions
