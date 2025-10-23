Feature: Landing Page Database Schema
  As a system
  I want to store landing page content in the database
  So that new variations can be added without code changes

  Scenario: Create landing page
    Given the database is connected
    When I insert a landing page with slug "test-page"
    Then the landing page should be retrievable by slug
    And the page should have all required fields

  Scenario: Create landing page sections
    Given a landing page exists with id "test-page-uuid"
    When I insert sections of type "pain_point" and "benefit"
    Then the sections should be ordered correctly
    And the sections should contain JSONB data

  Scenario: Query landing pages by category
    Given landing pages exist with categories "REPLACEMENT" and "COMPLEMENTARY"
    When I query for "REPLACEMENT" pages
    Then I should only get REPLACEMENT pages
    And the pages should be ordered by created date
