Feature: Performance Optimization
  As a system
  I want optimized performance
  So that operations are fast at scale

  Scenario: Filter 100K cards in under 50ms
    Given I have 100,000 cards in the system
    And cards have various tag combinations
    When I perform complex filtering
    Then results should return in under 50ms
    And memory usage should stay under 100MB
    And CPU usage should stay reasonable

  Scenario: Concurrent operations
    Given I have 10 concurrent users
    When they all perform operations simultaneously
    Then response times should remain consistent
    And no race conditions should occur
    And database connections should be pooled

  Scenario: Cache effectiveness
    Given I perform the same query multiple times
    When cache is enabled
    Then subsequent queries should be faster
    And cache hit rate should exceed 80%
    And cache invalidation should work correctly
