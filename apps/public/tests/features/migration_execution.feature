Feature: Execute Content Migration
  As a system administrator
  I want to run migration script once
  So that all landing page content is in the database

  Scenario: Run migration script
    Given the database is empty
    When I execute the migration script
    Then 7 landing pages should be inserted
    And all sections should be linked correctly
    And no duplicate slugs should exist

  Scenario: Verify content retrieval
    Given migration has completed
    When I query for slug "trello-performance"
    Then I should get the complete page with all sections
    And sections should be in order_index order
    And JSONB data should be parseable

  Scenario: Idempotency check
    Given migration has already run
    When I attempt to run migration again
    Then it should detect existing content
    And not create duplicates
    And exit gracefully
