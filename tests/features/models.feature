Feature: Basic Model Validation
  As a developer
  I want to ensure models are valid and immutable
  So that data integrity is maintained

  Scenario: Creating a valid card summary
    Given I have card data with title "Test Card" and tags "test,sample"
    When I create a CardSummary instance
    Then the card should have the correct title and tags
    And the card should be immutable

  Scenario: Creating a valid workspace
    Given I have workspace data with name "Test Workspace" and owner "user-123"
    When I create a Workspace instance
    Then the workspace should have the correct name and owner
    And the workspace should be immutable

  Scenario: Card with frozen tags
    Given I have a card with tags "video,urgent"
    When I try to modify the tags
    Then the modification should fail
    And the original tags should remain unchanged
