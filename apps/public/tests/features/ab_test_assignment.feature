Feature: A/B Test Assignment Logic
  As a system
  I want to assign visitors to A/B test variants
  So that I can measure conversion rate differences

  Scenario: Assign session to active A/B test variant
    Given an active A/B test exists with 50/50 traffic split
    And two variants exist for the test
    When I request variant assignment for a new session
    Then a variant should be assigned deterministically
    And the session should be linked to the variant

  Scenario: Deterministic assignment based on session ID
    Given an active A/B test with variants
    When I request assignment for the same session twice
    Then the same variant should be returned both times

  Scenario: Respect traffic split weights
    Given an A/B test with 70/30 split
    When I assign 1000 sessions to variants
    Then approximately 700 sessions should get variant A
    And approximately 300 sessions should get variant B
    And the distribution should be within 5% margin

  Scenario: No active test returns None
    Given no active A/B tests exist
    When I request variant assignment
    Then no variant should be assigned
    And the session should proceed without A/B test tracking
