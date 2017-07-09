Feature: Delete stack

  Scenario: delete a stack that exists
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    When the user deletes stack "1/A"
    Then stack "1/A" does not exist

  Scenario: delete a stack that does not exist
    Given stack "1/A" does not exist
    When the user deletes stack "1/A"
    Then stack "1/A" does not exist
