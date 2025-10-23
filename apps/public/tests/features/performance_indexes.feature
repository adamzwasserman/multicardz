Feature: Database Performance Indexes
  As a system administrator
  I want comprehensive database indexes
  So that all queries perform efficiently even with large data volumes

  Scenario: Missing indexes are identified
    Given I analyze the database schema
    When I check for missing indexes on frequently queried columns
    Then I should find missing indexes for browser_fingerprint lookup
    And I should find missing indexes for a_b_variant_id lookups
    And I should find missing indexes for conversion_funnel created timestamps
    And I should find missing indexes for funnel_stage with user_id combinations

  Scenario: Create performance indexes
    Given the database has the base schema
    When I create the performance optimization indexes
    Then an index should exist on analytics_sessions.browser_fingerprint
    And an index should exist on analytics_sessions.a_b_variant_id
    And an index should exist on conversion_funnel.created DESC
    And a composite index should exist on conversion_funnel (user_id, funnel_stage, created)
    And a composite index should exist on conversion_funnel (session_id, funnel_stage, created)
    And an index should exist on analytics_sessions.last_seen DESC

  Scenario: Query performance test - Session lookup by fingerprint
    Given the database has 10000 analytics sessions
    And 5000 sessions have browser fingerprints
    When I query for sessions by browser_fingerprint
    Then the query should complete in less than 50ms
    And the query plan should show index scan on browser_fingerprint

  Scenario: Query performance test - Funnel stage filtering
    Given the database has 50000 conversion funnel records
    And records span multiple funnel stages
    When I query for specific funnel_stage with date ordering
    Then the query should complete in less than 100ms
    And the query plan should show index scan on funnel_stage and created

  Scenario: Query performance test - User progression tracking
    Given the database has 20000 users with funnel records
    And each user has 1-4 funnel stages
    When I query for all stages of 100 random users
    Then the query should complete in less than 200ms
    And the query plan should show index scan on user_id and funnel_stage

  Scenario: Index size validation
    Given all performance indexes are created
    When I check the total index size
    Then the total index overhead should be less than 30% of table data size
    And each index should have reasonable selectivity
    And no duplicate or redundant indexes should exist
