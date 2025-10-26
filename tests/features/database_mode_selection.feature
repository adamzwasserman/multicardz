Feature: Database Mode Selection
  As a user
  I want to select different database modes
  So that I can choose my privacy level

  Scenario: Select privacy mode with subscription
    Given I have a premium subscription
    When I select privacy mode
    Then the database should operate in privacy mode
    And all content should be stored locally

  Scenario: Select normal mode as default
    Given I have a standard subscription
    When I access the application
    Then the database should operate in normal mode
    And queries should go to the server

  Scenario: Reject privacy mode without subscription
    Given I have a standard subscription
    When I try to select privacy mode
    Then I should see a subscription upgrade prompt
    And the mode should remain as normal
