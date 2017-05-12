Feature: Create stack

  Scenario: create new stack
    Given stack "A" does not exist
    When the user creates stack "A"
    Then stack "A" exists in "CREATE_COMPLETE" state

  Scenario: create a stack that already exists
    Given stack "A" exists in "CREATE_COMPLETE" state
    When the user creates stack "A"
    Then stack "A" exists in "CREATE_COMPLETE" state

  Scenario: create new stack that has previously failed
    Given stack "A" exists in "CREATE_FAILED" state
    When the user creates stack "A"
    Then stack "A" exists in "CREATE_COMPLETE" state
