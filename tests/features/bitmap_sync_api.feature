Feature: Bitmap Sync API
  As the system
  I want to sync bitmaps between browser and server
  So that set operations can be performed server-side

  Scenario: Sync card bitmap to server
    Given I have a card with bitmap in browser
    When I sync the bitmap to server
    Then the server should store only the bitmap
    And no content should be transmitted
    And the sync response should confirm success

  Scenario: Sync tag bitmap to server
    Given I have a tag with bitmap in browser
    When I sync the tag bitmap to server
    Then the server should store the tag bitmap
    And the tag name should not be transmitted
    And the sync response should confirm success

  Scenario: Handle sync failures gracefully
    Given the server is unavailable
    When I attempt to sync bitmaps
    Then the sync should fail gracefully
    And local operations should continue working
    And an appropriate error should be returned

  Scenario: Verify zero-trust UUID isolation
    Given I have cards from different workspaces
    When I sync bitmaps for each workspace
    Then each bitmap should be isolated by workspace_id
    And each bitmap should be isolated by user_id
    And cross-workspace queries should return empty results
