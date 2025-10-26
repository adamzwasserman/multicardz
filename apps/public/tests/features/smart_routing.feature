Feature: Smart Routing by Referrer
  As a system
  I want to automatically route visitors to relevant landing pages
  So that visitors see content tailored to their context

  Scenario: Route from Trello domain
    Given a visitor comes from "trello.com"
    When I request smart routing for the referrer
    Then I should be routed to "trello-performance" landing page
    And the routing reason should be "referrer_domain"

  Scenario: Route from search with competitor keyword
    Given a visitor comes from Google with query "notion alternative"
    When I request smart routing for the referrer
    Then I should be routed to "notion-performance" landing page
    And the routing reason should be "search_query"

  Scenario: Route from UTM campaign
    Given a visitor has UTM parameters with source "trello_refugees"
    When I request smart routing for the referrer
    Then I should be routed to "trello-performance" landing page
    And the routing reason should be "utm_campaign"

  Scenario: No specific referrer routes to default
    Given a visitor comes from a generic referrer
    When I request smart routing for the referrer
    Then I should be routed to the default landing page
    And the routing reason should be "default"

  Scenario: Direct traffic routes to default
    Given a visitor has no referrer
    When I request smart routing for the referrer
    Then I should be routed to the default landing page
    And the routing reason should be "direct"
