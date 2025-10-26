Feature: FastAPI Public Application
  As a system
  I want a FastAPI application for the public website
  So that I can serve landing pages and analytics

  Scenario: Start FastAPI application
    Given the FastAPI app is created
    When I start the test client
    Then the app should be accessible
    And health check endpoint should return 200

  Scenario: CORS configuration
    Given the app has CORS enabled
    When I make a request with Origin header
    Then CORS headers should be present
    And Access-Control-Allow-Origin should be set

  Scenario: Security headers
    Given the app is running
    When I request the health endpoint
    Then security headers should be present
    And X-Frame-Options should be DENY
    And X-Content-Type-Options should be nosniff
