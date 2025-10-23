Feature: Analytics Database Schema
  As a system
  I want to track visitor sessions and interactions
  So that I can analyze conversion funnels

  Scenario: Create analytics session
    Given the database is connected
    When I create a session with session_id
    Then the session should be retrievable
    And the session should track referrer and UTM params

  Scenario: Log page view
    Given a session exists
    When I log a page view with duration and scroll depth
    Then the page view should be associated with the session
    And duration and scroll depth should be stored

  Scenario: Track events
    Given a page view exists
    When I log click events with element selectors
    Then the events should be ordered by timestamp
    And element positions should be captured

  Scenario: Record mouse tracking data
    Given a page view exists
    When I batch insert 100 mouse coordinates
    Then all coordinates should be stored
    And performance should be acceptable
