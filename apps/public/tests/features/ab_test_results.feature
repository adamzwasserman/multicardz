Feature: A/B Test Results Calculation
  As a product manager
  I want to see conversion metrics for A/B test variants
  So that I can determine which variant performs better

  Scenario: Calculate conversion rates for A/B test
    Given an active A/B test with 2 variants
    And variant A has 100 sessions with 10 conversions
    And variant B has 100 sessions with 15 conversions
    When I calculate results for the A/B test
    Then variant A should show 10% conversion rate
    And variant B should show 15% conversion rate
    And variant B should be marked as leading

  Scenario: Calculate statistical significance
    Given an active A/B test with 2 variants
    And variant A has 1000 sessions with 100 conversions
    And variant B has 1000 sessions with 120 conversions
    When I calculate results for the A/B test
    Then the results should include statistical significance
    And the p-value should be calculated
    And confidence interval should be provided

  Scenario: Handle zero conversion scenarios
    Given an active A/B test with 2 variants
    And variant A has 50 sessions with 0 conversions
    And variant B has 50 sessions with 5 conversions
    When I calculate results for the A/B test
    Then variant A should show 0% conversion rate
    And variant B should show 10% conversion rate
    And the results should handle division by zero gracefully

  Scenario: Calculate average time to conversion
    Given an active A/B test with 2 variants
    And variant A has sessions with conversions at various times
    And variant B has sessions with conversions at various times
    When I calculate results for the A/B test
    Then each variant should show average time to conversion
    And the results should include conversion velocity metric

  Scenario: Compare multiple funnel stages
    Given an active A/B test with 2 variants
    And each variant has sessions at different funnel stages
    When I calculate results for the A/B test
    Then results should show conversion rate for each funnel stage
    And results should show drop-off rates between stages
    And results should identify bottleneck stages
