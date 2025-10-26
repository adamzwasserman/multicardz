Feature: Pydantic Models for Public Website
  As a system
  I want typed data models
  So that API requests/responses are validated

  Scenario: Landing page model validation
    Given a landing page dict with all fields
    When I create a LandingPage Pydantic model
    Then all fields should be validated
    And UUID fields should be proper UUIDs
    And timestamps should be datetime objects

  Scenario: Analytics event validation
    Given an analytics event dict
    When I create an AnalyticsEvent model
    Then required fields should be enforced
    And optional fields should be nullable
    And timestamp_ms should be a positive integer

  Scenario: Session creation validation
    Given session data with referrer and UTM params
    When I create an AnalyticsSession model
    Then UTM parameters should be extracted
    And referrer_domain should be parsed
    And session_id should be generated if not provided
