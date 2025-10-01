# tests/features/api_routes.feature
Feature: Zero-Trust API Routes
  As an API client
  I want workspace-isolated endpoints
  So that data is properly segregated

  Scenario: Get cards with workspace isolation
    Given I am authenticated with workspace_id
    When I request GET /api/cards
    Then I should only see cards from my workspace
    And response time should be under 100ms
    And proper caching headers should be set

  Scenario: Create card with auto-scoping
    Given I am authenticated with workspace_id
    When I POST to /api/cards without workspace_id
    Then the card should be created in my workspace
    And tag counts should be updated
    And response should include card_id

  Scenario: Unauthorized workspace access
    Given I am authenticated for workspace A
    When I try to access workspace B data
    Then I should receive 403 Forbidden
    And no data should be leaked
    And attempt should be logged
