Feature: Landing Page Routes
  As a user
  I want to view landing pages by slug
  So that I can learn about multicardz solutions

  Scenario: Retrieve active landing page by slug
    Given the database has landing pages
    When I request GET "/trello-performance"
    Then the response status should be 200
    And the response should contain the landing page data
    And the response should include all sections in order

  Scenario: Retrieve landing page with all section types
    Given the database has landing pages
    When I request GET "/trello-performance"
    Then the response should include pain_point sections
    And the response should include benefit sections
    And sections should be ordered by order_index

  Scenario: Handle non-existent slug
    Given the database has landing pages
    When I request GET "/non-existent-page"
    Then the response status should be 404
    And the response should contain an error message

  Scenario: Retrieve landing page with JSONB section data
    Given the database has landing pages
    When I request GET "/trello-performance"
    Then the response should contain parsed JSONB data
    And the data should be properly structured
    And all section fields should be accessible
