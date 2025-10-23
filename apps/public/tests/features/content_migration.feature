Feature: Landing Page Content Migration
  As a system
  I want to migrate landing page content from HTML to database
  So that content is manageable without code deployment

  Scenario: Parse JavaScript data from HTML
    Given the landing-variations-viewer-v3.html file
    When I extract the segmentsData JavaScript object
    Then I should have 2 replacement segments
    And I should have 5 complementary segments
    And each segment should have all required fields

  Scenario: Transform pain points to sections
    Given a landing page with 4 pain points
    When I transform to landing_page_sections format
    Then I should have 4 sections of type "pain_point"
    And each section should have data in JSONB format
    And sections should be ordered by index

  Scenario: Transform benefits to sections
    Given a landing page with 4 benefits
    When I transform to sections format
    Then each benefit should have title and description
    And sections should be ordered sequentially

  Scenario: Insert complete landing page
    Given parsed content for "trello-performance"
    When I insert into database
    Then the landing page should exist with slug
    And all sections should be linked
    And section count should match source data
