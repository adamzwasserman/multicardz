Feature: Jinja2 Template Rendering
  As a system
  I want to render landing pages using Jinja2 templates
  So that content from the database is displayed as HTML

  Scenario: Render landing page with all sections
    Given a landing page with headline and sections exists
    When I render the landing page template
    Then the HTML should contain the headline
    And the HTML should contain all pain points
    And the HTML should contain all benefits
    And the HTML should include the CTA button

  Scenario: Render pain point sections
    Given a landing page with 4 pain points
    When I render the pain points section
    Then each pain point should be displayed
    And pain points should be in correct order

  Scenario: Render benefit sections with icons
    Given a landing page with 4 benefits
    When I render the benefits section
    Then each benefit should have a title and description
    And benefits should be styled correctly

  Scenario: Render comparison metrics
    Given a landing page with competitor comparison
    When I render the comparison section
    Then competitor metrics should be displayed
    And multicardz metrics should be highlighted
