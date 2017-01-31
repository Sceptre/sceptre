Feature: test sceptre's continue-update-rollback

  Scenario: check sceptre continue update rollback
    Given stacks capable of getting to update rollback failed exist
    And a stack update has failed into update rollback failed
    When we continue update rollback
    Then the stack changes status
