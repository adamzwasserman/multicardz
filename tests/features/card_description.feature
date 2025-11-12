Feature: Card Description Management
  As a multicardz user
  I want to view and edit card descriptions
  So that I can add detailed information to my cards

  Background:
    Given the multicardz application is running on port 8011
    And I have a test workspace with sample cards

  Scenario: Display card description field
    Given I navigate to the workspace page
    When a card is rendered on the page
    Then the card should display a description field
    And the description field should be editable

  Scenario: Edit card description
    Given I navigate to the workspace page
    And a card with description "Original description" exists
    When I click on the card description field
    And I type "Updated description text"
    And I click outside the description field
    Then the card description should update to "Updated description text"
    And the description should be saved to the database

  Scenario: Save description on blur
    Given I navigate to the workspace page
    And a card with an empty description exists
    When I click on the card description field
    And I type "New card description"
    And I tab to the next field
    Then the description "New card description" should be saved
    And an API call to "/api/cards/update-content" should be made

  Scenario: Description persistence after page refresh
    Given I navigate to the workspace page
    And a card with card_id "test-card-001" exists
    When I update the card description to "Persistent description"
    And I wait for the save to complete
    And I refresh the page
    Then the card with card_id "test-card-001" should display "Persistent description"

  Scenario: Handle empty description
    Given I navigate to the workspace page
    And a card with description "Some text" exists
    When I clear the card description field
    And I click outside the description field
    Then the card description should be empty
    And the empty description should be saved to the database

  Scenario: Multiple cards with independent descriptions
    Given I navigate to the workspace page
    And cards with card_ids "card-001", "card-002", "card-003" exist
    When I update card "card-001" description to "First card description"
    And I update card "card-002" description to "Second card description"
    And I update card "card-003" description to "Third card description"
    Then card "card-001" should show "First card description"
    And card "card-002" should show "Second card description"
    And card "card-003" should show "Third card description"

  Scenario: Description field preserves formatting
    Given I navigate to the workspace page
    And a card exists
    When I enter description with newlines and spaces
    And I save the description
    Then the description should preserve the formatting

  Scenario: Cancel description edit with Escape key
    Given I navigate to the workspace page
    And a card with description "Original text" exists
    When I click on the card description field
    And I type "Modified text"
    And I press the Escape key
    Then the description should revert to "Original text"
    And no API call should be made

  Scenario: Description update error handling
    Given I navigate to the workspace page
    And the API endpoint is temporarily unavailable
    And a card exists
    When I update the card description to "Test description"
    And I click outside the description field
    Then an error should be logged to the console
    And the description field should remain editable

  Scenario: Long description text handling
    Given I navigate to the workspace page
    And a card exists
    When I enter a description with 1000 characters
    And I save the description
    Then the full description should be saved
    And the description should be retrievable from the database

  Scenario: Concurrent description edits
    Given I navigate to the workspace page with two browser tabs
    And the same card is visible in both tabs
    When I edit the description in tab 1 to "Tab 1 edit"
    And I edit the description in tab 2 to "Tab 2 edit"
    Then the last saved edit should persist
    And both tabs should reflect the final state after refresh

  Scenario: Description contenteditable attribute
    Given I navigate to the workspace page
    When a card is rendered
    Then the description element should have contenteditable="true"
    And the description element should have data-card-id attribute
    And the description element should have onblur="updateCardContent(this)"

  Scenario: updateCardContent function exists
    Given I navigate to the workspace page
    When the page JavaScript is loaded
    Then the updateCardContent function should be defined
    And calling updateCardContent should update the card content

  Scenario: Backend API endpoint exists
    Given the FastAPI application is running
    When I make a POST request to "/api/cards/update-content"
    And I provide payload containing card_id, content, and workspace_id
    Then the endpoint should return a success response
    And the card description should be updated in the database

  Scenario: CardRepository update_content method
    Given the CardRepository is initialized
    When I call update_content with valid parameters
    Then the card description should be updated in the database
    And the method should return True
    And the modified timestamp should be updated

  Scenario: Description in card template rendering
    Given a card with description "Template test description" exists
    When the card is rendered through Jinja2 template
    Then the template should include the card-description element
    And the element should display "Template test description"
    And the element should have correct CSS classes
