Feature: Analytics Session Creation API
  As a client-side analytics script
  I want to create analytics sessions via API
  So that visitor sessions can be tracked

  Scenario: Create new analytics session
    Given the FastAPI application is running
    When I POST to "/api/analytics/session" with session data
    Then the response status should be 201
    And the response should contain session_id
    And the session should be stored in the database

  Scenario: Create session with full UTM parameters
    Given the FastAPI application is running
    When I POST to "/api/analytics/session" with UTM parameters
    Then the response status should be 201
    And the session should have utm_source "google"
    And the session should have utm_campaign "trello-refugees"

  Scenario: Handle duplicate session creation
    Given an analytics session already exists
    When I POST to "/api/analytics/session" with the same session_id
    Then the response status should be 200
    And the last_seen timestamp should be updated

  Scenario: Extract referrer domain from URL
    Given the FastAPI application is running
    When I POST to "/api/analytics/session" with referrer "https://google.com/search"
    Then the session should have referrer_domain "google.com"

  Scenario: Reject invalid session data
    Given the FastAPI application is running
    When I POST to "/api/analytics/session" with invalid data
    Then the response status should be 422
    And the response should contain validation errors
