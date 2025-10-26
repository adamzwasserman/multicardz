Feature: Browser Database Service
  As a privacy-mode user
  I want a functional browser database service
  So that I can perform all database operations locally

  Scenario: Initialize browser database
    Given the browser database is not initialized
    When I initialize the browser database
    Then the database should be initialized successfully
    And the database should use OPFS storage
    And initialization should complete in less than 100ms

  Scenario: Execute query on browser database
    Given the browser database is initialized
    When I execute a SELECT query
    Then results should be returned successfully
    And no network request should be made

  Scenario: Execute transaction
    Given the browser database is initialized
    When I execute multiple statements in a transaction
    Then all statements should execute atomically
    And the database should remain consistent

  Scenario: Handle database errors
    Given the browser database is initialized
    When I execute an invalid query
    Then an appropriate error should be returned
    And the database should remain stable
