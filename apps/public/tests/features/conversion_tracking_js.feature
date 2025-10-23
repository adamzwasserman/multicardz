Feature: Conversion Tracking JavaScript
  As a marketing analyst
  I want to track conversion funnel stages
  So I can measure drop-off rates and optimize the funnel

  Background:
    Given the conversion tracking module is loaded
    And a session ID exists in localStorage

  Scenario: Track page view funnel stage
    When the page loads
    Then the "view" funnel stage should be tracked
    And the event should include the session_id
    And the event should include the landing_page_id

  Scenario: Track CTA click funnel stage
    Given a CTA button exists with data-cta="signup"
    When the user clicks the CTA button
    Then the "cta_click" funnel stage should be tracked
    And the event should include cta_id "signup"
    And the event should include button_text
    And the event should include button_position

  Scenario: Track multiple CTA clicks on same page
    Given multiple CTA buttons exist
    When the user clicks CTA button "hero-cta"
    And the user clicks CTA button "footer-cta"
    Then 2 "cta_click" funnel stages should be tracked
    And each event should have unique timestamps
    And each event should have different cta_ids

  Scenario: Funnel events are batched and submitted
    Given the batch size is configured to 5 events
    When 5 CTA clicks occur
    Then a batch submission to "/api/analytics/conversion" should occur
    And the batch should contain 5 funnel events
    And each event should have the correct structure

  Scenario: Flush conversion events on page unload
    Given 3 CTA clicks have been tracked
    When the beforeunload event fires
    Then the conversion events should be flushed immediately
    And the API should receive 3 events
