Feature: Auth0 Webhook Integration
  As the system
  I want to receive Auth0 user signup webhooks
  So that I can link analytics sessions to user accounts

  Scenario: Link session to user on signup
    Given an analytics session exists with fingerprint "fp123"
    And the session has no user_id linked
    When Auth0 sends a signup webhook with user_id "auth0|user123" and fingerprint "fp123"
    Then the session should be updated with user_id "auth0|user123"
    And a conversion_funnel record should be created with stage "signup"
    And the funnel record should link to the session

  Scenario: Handle signup with no matching session
    Given no analytics session exists with fingerprint "fp456"
    When Auth0 sends a signup webhook with user_id "auth0|user456" and fingerprint "fp456"
    Then the webhook should succeed with 200 status
    And no session should be updated
    And a conversion_funnel record should be created with stage "signup"
    And the funnel record should have user_id "auth0|user456"
    And the funnel record should have null session_id

  Scenario: Handle signup with existing user_id (already linked)
    Given an analytics session exists with fingerprint "fp789"
    And the session already has user_id "auth0|existing"
    When Auth0 sends a signup webhook with user_id "auth0|user789" and fingerprint "fp789"
    Then the webhook should succeed with 200 status
    And the session user_id should remain "auth0|existing"
    And no new funnel record should be created

  Scenario: Webhook authentication with valid token
    Given an analytics session exists with fingerprint "fp_secure"
    And a valid Auth0 webhook token exists
    When Auth0 sends an authenticated signup webhook with user_id "auth0|secure" and fingerprint "fp_secure"
    Then the webhook should succeed with 200 status
    And the session should be updated with user_id "auth0|secure"

  Scenario: Webhook authentication with invalid token
    Given an analytics session exists with fingerprint "fp_invalid"
    And an invalid Auth0 webhook token exists
    When Auth0 sends an authenticated signup webhook with user_id "auth0|invalid" and fingerprint "fp_invalid"
    Then the webhook should fail with 401 status
    And the session should not be updated

  Scenario: Batch webhook processing
    Given 5 analytics sessions exist with different fingerprints
    And none of the sessions have user_id linked
    When Auth0 sends a batch webhook with 5 user signups
    Then all 5 sessions should be updated with their respective user_ids
    And 5 conversion_funnel records should be created
    And all funnel records should have stage "signup"
