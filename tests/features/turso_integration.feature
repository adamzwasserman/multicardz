Feature: Turso Integration End-to-End
  As a user
  I want the complete Turso integration to work
  So that I can use different database modes effectively

  Background:
    Given the database is initialized
    And all required modules are imported

  Scenario: Complete privacy mode workflow
    Given I enable privacy mode
    When I create a card locally with name "Test Card" and tags "tag-1,tag-2"
    Then the card should exist in browser database
    When I sync the bitmap to server
    Then the server should store only the bitmap
    And no content should be transmitted

  Scenario: Mode switching between modes
    Given I am in normal mode
    When I switch to privacy mode
    Then the mode should change successfully
    And query routing should use browser database
    When I switch to dev mode
    Then the mode should change successfully
    And query routing should use dev database

  Scenario: Query routing in privacy mode
    Given I am in privacy mode
    And I have 3 cards in browser database
    When I query for cards with workspace_id "ws-1" and user_id "user-1"
    Then I should get 3 cards from browser database
    And no server request should be made

  Scenario: Bitmap operations integration
    Given I am in privacy mode
    And I have cards with bitmaps in browser database
    When I sync all bitmaps to server
    Then all bitmaps should be stored on server
    And no content fields should be transmitted
    When I query for cards by bitmap filter
    Then the server should return matching UUIDs only
    And the browser should resolve UUIDs to content

  Scenario: Error handling and offline functionality
    Given I am in privacy mode
    And the server is unavailable
    When I create a card locally
    Then the card should be created successfully
    And the sync should be queued
    When the server becomes available
    Then the queued sync should succeed
