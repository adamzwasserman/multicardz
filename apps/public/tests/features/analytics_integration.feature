Feature: Analytics JavaScript Integration
  As a marketing analyst
  I want all analytics modules to work together seamlessly
  So I can track complete user sessions with page views, interactions, mouse movements, and conversions

  Background:
    Given all analytics JavaScript modules are loaded
    And a session ID exists

  Scenario: Complete analytics stack initialization
    When a landing page loads
    Then analytics.js should create a session
    And mouse-tracking.js should start tracking
    And conversion-tracking.js should track the view stage
    And all modules should share the same session ID

  Scenario: Coordinated batch submission
    Given all analytics modules are tracking
    When the user performs multiple actions
    And 10 seconds pass
    Then analytics.js should submit page view and event batches
    And mouse-tracking.js should submit position batches
    And conversion-tracking.js should submit funnel event batches
    And all batches should include the same session ID

  Scenario: Graceful page unload
    Given all analytics modules have tracked data
    When the page is about to unload
    Then all modules should flush their queued events
    And all data should be submitted via sendBeacon
    And no data should be lost

  Scenario: Module independence
    Given analytics.js fails to load
    When the page loads
    Then mouse-tracking.js should still work
    And conversion-tracking.js should still work
    And each module should operate independently

  Scenario: Shared session management
    Given analytics.js creates a session
    When mouse-tracking.js initializes
    And conversion-tracking.js initializes
    Then all modules should use the same session ID
    And the session ID should persist in localStorage
    And the session ID should be in all API calls
