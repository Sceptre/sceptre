Feature: Delete stack

  Scenario: delete a stack that exists
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    When the user deletes stack "1/A"
    Then stack "1/A" does not exist

  Scenario: delete a stack that does not exist
    Given stack "1/A" does not exist
    When the user deletes stack "1/A"
    Then stack "1/A" does not exist

  Scenario: delete a stack that exists with ignore dependencies
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    When the user deletes stack "1/A" with ignore dependencies
    Then stack "1/A" does not exist

  Scenario: delete a stack that exists with dependencies ignoring dependencies
    Given stack "4/C" exists in "CREATE_COMPLETE" state 
    and stack "3/A" exists in "CREATE_COMPLETE" state 
    and stack "3/A" depends on stack "4/C"
    When the user deletes stack "4/C" with ignore dependencies
    Then stack "4/C" does not exist and stack "3/A" exists in "CREATE_COMPLETE"
