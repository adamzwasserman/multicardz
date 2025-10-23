Feature: Admin Dashboard Overview
  As a product manager
  I want to see analytics overview metrics
  So that I can track overall landing page performance

  Scenario: View dashboard overview with key metrics
    Given the analytics database has session data
    When I visit the admin dashboard overview page
    Then I should see total sessions count
    And I should see total page views count
    And I should see total conversions count
    And I should see overall conversion rate
    And I should see average session duration

  Scenario: View top performing landing pages
    Given multiple landing pages have different performance
    When I visit the admin dashboard overview page
    Then I should see a list of landing pages ranked by conversion rate
    And each landing page should show sessions count
    And each landing page should show conversion rate

  Scenario: View recent A/B test results
    Given there are active A/B tests with data
    When I visit the admin dashboard overview page
    Then I should see a list of active A/B tests
    And each test should show leading variant
    And each test should show statistical significance status

  Scenario: View traffic source breakdown
    Given sessions come from different referrer sources
    When I visit the admin dashboard overview page
    Then I should see traffic breakdown by source
    And I should see direct traffic percentage
    And I should see organic search percentage
    And I should see referral traffic percentage

  Scenario: Dashboard accessible only with authentication
    Given I am not authenticated
    When I try to access the admin dashboard
    Then I should be redirected to login page
    Or I should see an unauthorized error
