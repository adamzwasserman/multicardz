Feature: Database Storage Layer for Two-Tier Architecture
  As a MultiCardz system
  I want to persist cards using two-tier architecture
  So that I can efficiently load card summaries and details on-demand

  Background:
    Given a clean database connection
    And the database schema is initialized

  Scenario: Save and load CardSummary objects
    Given I have a CardSummary with title "Test Card" and tags "urgent,bug"
    When I save the CardSummary to the database
    Then I can load the CardSummary by ID
    And the loaded CardSummary has the correct title and tags
    And the CardSummary loads in under 10ms

  Scenario: Two-tier lazy loading of CardDetail
    Given I have a CardSummary saved in the database
    And the CardSummary has associated CardDetail with content "Full content here"
    When I save the CardDetail to the database
    Then I can load CardDetail on-demand by card ID
    And the CardDetail contains the full content
    And CardDetail loading is separate from CardSummary loading

  Scenario: Tag count tuple generation for optimization
    Given I have multiple cards with overlapping tags:
      | title  | tags          |
      | Card 1 | urgent,bug    |
      | Card 2 | urgent,feature|
      | Card 3 | bug,low       |
      | Card 4 | urgent,high   |
    When I request tag count tuples from the database
    Then I receive tuples in the format (tag, count):
      | tag     | count |
      | urgent  | 3     |
      | bug     | 2     |
      | feature | 1     |
      | low     | 1     |
      | high    | 1     |
    And the tuples are sorted by count ascending for selectivity optimization

  Scenario: User preferences persistence
    Given I have UserPreferences for user "user123"
    When I save the preferences to the database
    Then I can load the preferences by user ID
    And the preferences contain all view, theme, tag, and workspace settings
    And preferences loading takes under 5ms

  Scenario: Bulk card loading for set operations
    Given I have 1000 CardSummary objects in the database
    When I load all CardSummary objects for workspace filtering
    Then all cards are loaded in under 75ms
    And the loaded cards can be used with set operations
    And CardDetail objects are not loaded automatically

  Scenario: Database transaction rollback on error
    Given I have started a database transaction
    When I attempt to save invalid card data
    And an error occurs during save
    Then the transaction is rolled back
    And no partial data is persisted
    And the database remains in a consistent state
