Feature: Core Analytics JavaScript
  As a public website
  I want to track page views and user interactions
  So that I can measure conversion funnel effectiveness

  Scenario: Initialize analytics session
    Given the analytics JavaScript is loaded
    When the page loads
    Then a session_id should be created or retrieved from storage
    And the session should track referrer URL
    And the session should track UTM parameters

  Scenario: Track page view
    Given an analytics session exists
    When a page view is tracked
    Then the page view should include URL
    And the page view should include viewport dimensions
    And the page view should include timestamp

  Scenario: Track click events
    Given an analytics session exists
    When a user clicks an element with class "cta-button"
    Then the event should capture element selector
    And the event should capture element text
    And the event should capture element position
    And the event should capture timestamp

  Scenario: Track scroll depth
    Given an analytics session exists
    When a user scrolls to 75% of page
    Then the scroll depth should be tracked
    And the scroll depth should be associated with page view

  Scenario: Batch event collection
    Given multiple events have been tracked
    When 5 seconds elapse or 10 events are collected
    Then all events should be batched together
    And a single API call should be made
    And the events should be cleared from buffer
