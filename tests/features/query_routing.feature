Feature: Query Routing
  As the application
  I want to route queries appropriately
  So that content and bitmap operations are separated

  Scenario: Route content query to browser database
    Given I am in privacy mode
    When I query for card content
    Then the query should execute locally
    And no server request should be made

  Scenario: Route bitmap operation to server
    Given I am in privacy mode
    When I perform a set operation
    Then the operation should execute on server
    And only UUIDs should be returned

  Scenario: Combine local and server results
    Given I have cards in browser and bitmaps on server
    When I perform a filtered query
    Then server should return matching UUIDs
    And browser should resolve UUIDs to content

  Scenario: Route queries in normal mode to server
    Given I am in normal mode
    When I query for card content
    Then the query should execute on server
    And no browser database should be used
