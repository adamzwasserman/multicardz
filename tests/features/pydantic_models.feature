Feature: Pydantic Data Models
  As a developer
  I want validated data models
  So that data integrity is maintained

  Scenario: Create valid Card model
    Given I have card data with required fields
    When I create a Card model instance
    Then the model should validate successfully
    And UUIDs should be generated automatically
    And tag arrays should default to empty

  Scenario: Validate Tag model with bitmap
    Given I have tag data with bitmap field
    When I create a Tag model instance
    Then the bitmap should be an integer
    And card_count should default to 0
    And the model should be frozen

  Scenario: Reject invalid workspace isolation
    Given I have card data without workspace_id
    When I try to create a Card model
    Then validation should fail
    And error should mention missing workspace_id
