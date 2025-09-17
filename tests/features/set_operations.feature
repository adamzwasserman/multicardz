Feature: Polymorphic Set Operations
  As a developer
  I want to perform complex tag filtering operations efficiently
  So that users can find cards quickly using set theory

  Background:
    Given I have a collection of CardSummary objects with various tags
    And tags are available with their card counts for optimization

  Scenario: Basic intersection operation
    Given I have cards with tags:
      | card_id | tags                    |
      | CARD001 | urgent,bug,backend      |
      | CARD002 | urgent,feature,frontend |
      | CARD003 | bug,backend             |
      | CARD004 | urgent,bug              |
    When I apply intersection operation with tags ["urgent", "bug"]
    Then I should get cards ["CARD001", "CARD004"]
    And the operation should complete in less than 10ms

  Scenario: Basic union operation
    Given I have cards with tags:
      | card_id | tags                    |
      | CARD001 | urgent,bug,backend      |
      | CARD002 | urgent,feature,frontend |
      | CARD003 | bug,backend             |
      | CARD004 | feature,design          |
    When I apply union operation with tags ["urgent", "design"]
    Then I should get cards ["CARD001", "CARD002", "CARD004"]
    And the operation should complete in less than 10ms

  Scenario: Polymorphic operation sequence
    Given I have cards with tags:
      | card_id | tags                         |
      | CARD001 | urgent,bug,backend,assigned  |
      | CARD002 | urgent,feature,frontend      |
      | CARD003 | bug,backend,assigned         |
      | CARD004 | urgent,bug,resolved          |
      | CARD005 | feature,backend,assigned     |
    And tags have the following counts:
      | tag      | count |
      | urgent   | 3     |
      | bug      | 3     |
      | assigned | 3     |
      | resolved | 1     |
      | backend  | 3     |
    When I apply operations in sequence:
      | operation    | tags              |
      | intersection | urgent,bug        |
      | difference   | resolved          |
    Then I should get cards ["CARD001"]
    And tags should be processed in order of selectivity
    And the operation should complete in less than 10ms

  Scenario: Short-circuit on empty result
    Given I have cards with tags:
      | card_id | tags              |
      | CARD001 | urgent,bug        |
      | CARD002 | feature,frontend  |
    When I apply operations in sequence:
      | operation    | tags              |
      | intersection | urgent,bug        |
      | intersection | nonexistent       |
    Then the operation should short-circuit after the second step
    And I should get an empty result set
    And the operation should complete in less than 5ms

  Scenario: Cache effectiveness for repeated operations
    Given I have 1000 CardSummary objects with random tags
    When I apply the same operation sequence twice:
      | operation    | tags              |
      | intersection | urgent,important  |
      | union        | high,medium       |
    Then the second execution should be faster than the first
    And cache hit rate should be recorded
    And both operations should complete in less than 10ms

  Scenario: Performance with large dataset
    Given I have 5000 CardSummary objects with random tags
    When I apply a complex operation sequence:
      | operation    | tags                    |
      | intersection | priority,urgent         |
      | union        | high,medium,low         |
      | difference   | resolved,completed      |
    Then the operation should complete in less than 25ms
    And memory usage should remain stable
    And intermediate results should be optimized

  Scenario: Tag count optimization
    Given I have cards with tags:
      | card_id | tags                    |
      | CARD001 | common,rare,unique      |
      | CARD002 | common,rare             |
      | CARD003 | common                  |
    And tags have the following counts:
      | tag    | count |
      | common | 3     |
      | rare   | 2     |
      | unique | 1     |
    When I apply intersection operation with tags ["rare", "unique", "common"]
    Then tags should be processed in order: unique, rare, common
    And the most selective tag should be processed first
    And the operation should complete efficiently

  Scenario: User preference integration
    Given I have cards and user preferences for ordering
    And user prefers cards ordered by "modified_at DESC"
    When I apply set operations and get results
    Then results should be ordered according to user preferences
    And preference application should add less than 1ms overhead

  Scenario: Operation validation
    Given I have cards with tags
    When I apply an invalid operation type "nonexistent"
    Then I should get a clear error message
    And the system should suggest valid operation types
    And no partial results should be returned

  Scenario: Memory efficiency with large results
    Given I have 10000 CardSummary objects
    When I apply operations that return 5000 results
    Then memory usage should be proportional to result size
    And garbage collection should be minimal
    And CardSummary objects should remain immutable
