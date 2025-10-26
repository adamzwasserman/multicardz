Feature: Funnel Stage Tracking Service
  As a product manager
  I want to analyze user progression through the conversion funnel
  So that I can identify drop-off points and optimize conversion rates

  Background:
    Given the database is empty
    And I have a test landing page
    And I have analytics sessions with funnel stages

  Scenario: Get overall funnel metrics
    When I request overall funnel metrics
    Then I should see funnel stage counts
    And I should see conversion rates between stages
    And I should see total funnel duration statistics

  Scenario: Get funnel progression for a specific user
    Given a user "auth0|user123" has progressed through multiple stages
    When I request funnel progression for user "auth0|user123"
    Then I should see all stages the user completed
    And I should see timestamps for each stage
    And I should see time between stages

  Scenario: Get funnel drop-off analysis
    Given I have 100 sessions at landing stage
    And 60 sessions progressed to signup
    And 40 sessions progressed to first_card
    And 20 sessions progressed to upgrade
    When I request funnel drop-off analysis
    Then I should see 40% drop-off between landing and signup
    And I should see 33.33% drop-off between signup and first_card
    And I should see 50% drop-off between first_card and upgrade

  Scenario: Get average time between funnel stages
    Given users have various completion times between stages
    When I request average funnel stage durations
    Then I should see average time from landing to signup
    And I should see average time from signup to first_card
    And I should see average time from first_card to upgrade

  Scenario: Get funnel cohort analysis by date
    Given I have funnel data for the past 30 days
    When I request funnel cohort analysis for "2025-10-20"
    Then I should see signup conversions for that cohort
    And I should see retention to first_card for that cohort
    And I should see upgrade conversions for that cohort

  Scenario: Get funnel performance by landing page
    Given I have multiple landing pages
    And each page has different conversion rates
    When I request funnel performance by landing page
    Then I should see conversion rates for each page
    And pages should be ranked by conversion performance
