Feature: Automatic Tag Count Maintenance
  As a system
  I want automatic tag count updates
  So that counts are always accurate

  Scenario: Increment count on card creation
    Given I have a tag with count 5
    When I create a card with that tag
    Then the tag count should be 6
    And the update should be atomic
    And no manual count update should be possible

  Scenario: Decrement count on card deletion
    Given I have a tag with count 10
    When I delete a card with that tag
    Then the tag count should be 9
    And count should never go below 0
    And soft delete should be used

  Scenario: Update counts on tag reassignment
    Given I have a card with tags A and B
    When I change tags to B and C
    Then tag A count should decrease by 1
    And tag C count should increase by 1
    And tag B count should remain the same
