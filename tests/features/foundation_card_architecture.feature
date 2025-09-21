Feature: Two-Tier Card Architecture Foundation
  As a system architect
  I want efficient two-tier card representation
  So that the system supports 500,000+ cards with sub-millisecond operations

  Scenario: CardSummary optimized for list operations
    Given I have a collection of cards requiring fast list rendering
    When I create CardSummary instances with minimal data
    Then each summary should consume approximately 50 bytes
    And list operations should complete in <1ms for 10,000 cards

  Scenario: CardDetail lazy loading for expanded views
    Given I have CardSummary instances displayed in a list
    When I request detailed view for specific cards
    Then CardDetail should load on-demand with complete metadata
    And loading should not affect list performance

  Scenario: Immutable card structures with frozenset tags
    Given I create card instances with tag collections
    When I attempt to modify card properties
    Then cards should be immutable by design
    And tags should be frozenset for set theory operations

  Scenario: Performance validation with large datasets
    Given I have 100,000 card instances
    When I perform filtering operations using set theory
    Then operations should complete within 26x performance target
    And memory usage should remain below optimization thresholds