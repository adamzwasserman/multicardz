Feature: Two-Tier Card Model System
  As a developer
  I want to ensure CardSummary and CardDetail work correctly
  So that performance is optimized with lazy loading

  Scenario: Creating a CardSummary with minimal data
    Given I have card summary data with title "Quick Card" and tags "quick,test"
    When I create a CardSummary instance
    Then the card summary should have the correct data
    And the card summary should be immutable
    And the card summary should have timestamps

  Scenario: Creating a CardDetail with extended data
    Given I have card detail data with id "CARD1234" and content "Detailed content here"
    When I create a CardDetail instance
    Then the card detail should have the correct data
    And the card detail should be immutable
    And the card detail should have version tracking

  Scenario: Creating an Attachment with file data
    Given I have attachment data with filename "test.pdf" and size 1024
    When I create an Attachment instance
    Then the attachment should have the correct metadata
    And the attachment should be immutable

  Scenario: Creating a UserTier with storage quotas
    Given I have user tier data for tier "pro" with storage quota 10GB
    When I create a UserTier instance
    Then the user tier should have correct storage limits
    And the user tier should calculate storage usage percentage
    And the user tier should be immutable

  Scenario: UserTier storage calculations
    Given I have a UserTier with 10GB quota and 5GB usage
    When I check the storage calculations
    Then the quota should be correctly converted to bytes
    Then the usage percentage should be 50%
