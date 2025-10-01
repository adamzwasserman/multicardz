Feature: Database Connection Management
  As a system
  I want proper database connection management
  So that connections are isolated and secure

  Scenario: Create workspace-isolated connection
    Given I have a workspace_id and user_id
    When I request a database connection
    Then the connection should be workspace-specific
    And queries should be automatically scoped
    And the connection should use context manager

  Scenario: Fallback from Turso to SQLite
    Given Turso is unavailable
    When I request a database connection
    Then the system should use SQLite fallback
    And functionality should remain the same
    And a warning should be logged

  Scenario: Connection pool management
    Given I have multiple concurrent requests
    When connections are requested
    Then connections should be pooled
    And pool size should not exceed maximum
    And connections should be recycled properly
