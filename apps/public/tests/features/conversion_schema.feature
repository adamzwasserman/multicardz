Feature: Conversion Funnel Database Schema
  As a system
  I want to track user progression through conversion stages
  So that I can measure funnel performance

  Scenario: Track funnel stage
    Given a session exists
    When I log a "view" stage
    Then the stage should be recorded with timestamp
    And I can query all stages for the session

  Scenario: Link session to user
    Given a session with funnel stages exists
    When an account is created with user_id
    Then the session should be linked to the user
    And all subsequent stages should include user_id

  Scenario: Calculate conversion rates
    Given 100 sessions with various funnel stages
    When I calculate conversion from "view" to "account_create"
    Then the conversion rate should be calculable
    And abandonment rate should be measurable

  Scenario: Create A/B test
    Given I define a test with 50/50 split
    When I assign sessions to variants
    Then assignments should be deterministic
    And traffic should split approximately 50/50

  Scenario: Create heatmap bucket
    Given a landing page exists
    When I record clicks in 10px buckets
    Then buckets should aggregate click counts
    And unique constraint should prevent duplicates
    And hover duration should be tracked
