Feature: End-to-End System Validation
  As a product manager
  I want to validate the complete system integration
  So that all features work together seamlessly from landing to conversion

  Scenario: Complete user journey - Landing to Signup
    Given the system is fully operational
    And a landing page exists with slug "trello-alternative"
    When a new user visits the landing page
    And the analytics JavaScript tracks the page view
    And the user's session is created with UTM parameters
    And the user clicks the signup button
    And a webhook is received for account creation
    Then the analytics session should be linked to the user account
    And a funnel record should exist for "landing" stage
    And a funnel record should exist for "signup" stage
    And the conversion funnel should show progression

  Scenario: A/B test variant assignment and tracking
    Given an active A/B test exists with 2 variants
    And both variants have landing pages
    When 100 users visit the landing page
    Then users should be distributed between variants
    And each session should have a variant assigned
    And variant performance metrics should be calculable
    And conversion rates should differ by variant

  Scenario: Complete conversion funnel from landing to upgrade
    Given a user session exists with analytics data
    When the user completes the signup process
    And creates their first card
    And upgrades to a paid subscription
    Then funnel records should exist for all 4 stages
    And stage timestamps should be in correct order
    And average stage durations should be calculable
    And the conversion rate should be 100%

  Scenario: Dashboard analytics aggregation
    Given the system has 1000 sessions across 10 landing pages
    And 500 users have signed up
    And 100 users have created cards
    And 20 users have upgraded
    When I request the dashboard overview
    Then overall metrics should show correct totals
    And funnel conversion rates should be accurate
    And landing page performance should be ranked
    And A/B test results should be available

  Scenario: Real-time analytics ingestion and query
    Given the analytics API is accepting events
    When I send 100 page view events
    And I immediately query for dashboard metrics
    Then all events should be ingested
    And metrics should reflect the new data
    And query response time should be <200ms
    And data consistency should be maintained

  Scenario: Performance under realistic load
    Given the database has 100000 sessions
    And the database has 500000 analytics events
    When 50 concurrent users access the system
    Then all requests should succeed
    And average response time should be <500ms
    And database indexes should be utilized
    And no timeouts should occur

  Scenario: Cross-device conversion attribution
    Given a user visits from mobile without account
    And the session has a browser fingerprint
    When the user signs up from desktop
    And the signup webhook provides the fingerprint
    Then the original session should be linked to the user
    And both mobile and desktop sessions should be attributed
    And the complete journey should be trackable

  Scenario: Data integrity validation
    Given the system has been running for 30 days
    When I validate all foreign key relationships
    And I check for orphaned records
    And I verify all timestamps are valid
    Then no data integrity violations should exist
    And all sessions should have landing pages
    And all funnel records should have valid stages
    And all webhooks should have processed successfully
