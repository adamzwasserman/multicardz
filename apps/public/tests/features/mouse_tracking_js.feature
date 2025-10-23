Feature: Mouse Tracking JavaScript for Session Replay
  As a public website
  I want to record mouse movements and interactions
  So that I can replay user sessions for UX analysis

  Scenario: Track mouse movement
    Given the mouse tracking JavaScript is loaded
    When a user moves the mouse
    Then mouse coordinates should be captured
    And timestamps should be recorded
    And coordinates should be relative to document

  Scenario: Sample mouse positions efficiently
    Given mouse tracking is active
    When the user moves the mouse continuously
    Then mouse positions should be sampled at intervals
    And not every single mouse movement should be recorded
    And sampling rate should be configurable (default 100ms)

  Scenario: Batch mouse tracking data
    Given 50 mouse positions have been tracked
    When the batch threshold is reached
    Then all positions should be batched together
    And a single API call should be made
    And the buffer should be cleared

  Scenario: Track mouse clicks with coordinates
    Given mouse tracking is active
    When a user clicks on the page
    Then the click position should be recorded
    And the click should be marked as a special event
    And click coordinates should match mouse position

  Scenario: Respect privacy settings
    Given mouse tracking is initialized
    When tracking is disabled via privacy setting
    Then mouse movements should not be recorded
    And no API calls should be made for mouse data
