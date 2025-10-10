Feature: Bitmap Filter Endpoint
  As the server
  I want to perform bitmap filtering operations
  So that clients can query card sets using bitmaps

  Scenario: Filter cards by single tag bitmap
    Given I have card bitmaps in the database
    When I request cards with tag bitmap "111"
    Then the server should return matching card UUIDs
    And no content should be returned
    And the response time should be under 100ms

  Scenario: Filter cards using intersection of multiple tags
    Given I have card bitmaps in the database
    When I request cards with tag bitmaps "111" AND "222"
    Then the server should return cards matching both tags
    And the operation should use bitmap intersection
    And no content should be returned

  Scenario: Filter cards using union of multiple tags
    Given I have card bitmaps in the database
    When I request cards with tag bitmaps "111" OR "222"
    Then the server should return cards matching either tag
    And the operation should use bitmap union
    And no content should be returned

  Scenario: Filter cards with exclusion (NOT operation)
    Given I have card bitmaps in the database
    When I request cards with tag bitmap "111" NOT "222"
    Then the server should return cards with tag 111 but not tag 222
    And the operation should use bitmap difference
    And no content should be returned

  Scenario: Handle complex nested bitmap operations
    Given I have card bitmaps in the database
    When I request cards with complex filter "(111 AND 222) OR (333 NOT 444)"
    Then the server should compute the nested operations correctly
    And return only the matching card UUIDs
    And no content should be returned

  Scenario: Enforce zero-trust UUID isolation
    Given I have card bitmaps for multiple workspaces
    When I request cards with workspace_id "ws-1" and user_id "user-1"
    Then the server should return only cards for that workspace and user
    And cards from other workspaces should be excluded

  Scenario: Return empty result for no matches
    Given I have card bitmaps in the database
    When I request cards with tag bitmap "999" that has no matches
    Then the server should return an empty card list
    And the response should indicate 0 matches
    And no content should be returned
