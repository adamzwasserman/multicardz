Feature: Connection Logic Update
  As the database system
  I want to route connections based on database mode
  So that queries are executed in the appropriate context

  Scenario: Route connection to browser database in privacy mode
    Given the database mode is set to "privacy"
    When I request a database connection
    Then the connection should route to the browser database
    And no server connection should be established

  Scenario: Route connection to server database in normal mode
    Given the database mode is set to "normal"
    When I request a database connection
    Then the connection should route to the server database
    And the connection URL should be the Turso cloud URL

  Scenario: Route connection to local database in dev mode
    Given the database mode is set to "dev"
    When I request a database connection
    Then the connection should route to the local database
    And the connection URL should be the local development URL

  Scenario: Handle connection mode switch from normal to privacy
    Given the database mode is set to "normal"
    And a connection is established
    When I switch the database mode to "privacy"
    And I request a new database connection
    Then the connection should route to the browser database
    And the previous server connection should be closed

  Scenario: Validate connection parameters based on mode
    Given the database mode is set to "privacy"
    When I request a database connection with server parameters
    Then the connection should reject server parameters
    And return a browser database connection instead
