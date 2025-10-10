Feature: UI Mode Switching
  As a user
  I want to switch between database modes via the UI
  So that I can choose my privacy level and manage my data

  Scenario: Display current mode in UI
    Given I am in normal mode
    When I view the settings panel
    Then I should see the current mode as "normal"
    And I should see mode description and features

  Scenario: Switch from normal to privacy mode with subscription
    Given I am in normal mode
    And I have a premium subscription
    When I select privacy mode in the UI
    Then the mode should switch to privacy
    And my data should migrate to browser database
    And I should see privacy mode confirmation

  Scenario: Prevent privacy mode switch without subscription
    Given I am in normal mode
    And I have a standard subscription
    When I attempt to select privacy mode in the UI
    Then I should see a subscription upgrade prompt
    And the mode should remain as normal
    And no data should be migrated

  Scenario: Switch from privacy to normal mode
    Given I am in privacy mode
    When I select normal mode in the UI
    Then the mode should switch to normal
    And my browser data should sync to server
    And I should see normal mode confirmation

  Scenario: Persist mode selection across sessions
    Given I am in privacy mode
    When I refresh the browser
    Then the mode should still be privacy
    And all local data should be available

  Scenario: Display mode-specific features in UI
    Given I am in privacy mode
    When I view the settings panel
    Then I should see privacy mode features
    And I should see browser database statistics
    And I should see offline capability indicator
