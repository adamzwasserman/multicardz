Feature: Card Creation Integration with Browser Database
  As a user in privacy mode
  I want to create cards locally in my browser
  So that my card content never reaches the server

  Background:
    Given the browser database is initialized
    And I am in privacy mode

  Scenario: Create card locally in privacy mode
    When I create a new card with name "Test Card" and tags "tag1,tag2"
    Then the card should be stored in browser database
    And the card bitmap should be calculated
    And the bitmap should sync to server
    And the card content should not be transmitted to server
    And the card should appear in the grid

  Scenario: Create card with dimensional tags from grid cell
    Given I have row tag "Priority" and column tag "Work"
    When I create a card from grid cell
    Then the card should include dimensional tags
    And the card should be stored locally
    And the card should appear in the correct grid cell

  Scenario: Create card in normal mode
    Given I am in normal mode
    When I create a new card with name "Test Card" and tags "tag1,tag2"
    Then the card should be stored on server
    And the card should appear in the grid

  Scenario: Create card with bitmap calculation
    When I create a card with tags "javascript,react,tutorial"
    Then the card bitmap should be calculated from tag bitmaps
    And the bitmap should be synced to server
    And the card content should remain local

  Scenario: Handle card creation failure gracefully
    Given the browser database is unavailable
    When I attempt to create a card
    Then I should see an error message
    And the UI should remain functional
    And no partial data should be synced

  Scenario: Auto-focus new card title
    When I create a new card
    Then the card should be created successfully
    And the card title should be focused for editing
    And the card should be visible in the grid
