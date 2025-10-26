Feature: Analytics Page View API
  As a client-side analytics script
  I want to log page views via API
  So that visitor page views can be tracked

  Scenario: Create new page view
    Given the FastAPI application is running
    When I POST to "/api/analytics/page-view" with page view data
    Then the response status should be 201
    And the response should contain page_view_id
    And the page view should be stored in the database

  Scenario: Log page view with duration and scroll depth
    Given the FastAPI application is running  
    When I POST to "/api/analytics/page-view" with duration 45000 and scroll_depth 75
    Then the response status should be 201
    And the page view should have duration_ms 45000
    And the page view should have scroll_depth_percent 75

  Scenario: Reject invalid page view data
    Given the FastAPI application is running
    When I POST to "/api/analytics/page-view" with invalid data
    Then the response status should be 422
