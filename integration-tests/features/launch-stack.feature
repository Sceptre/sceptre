Feature: Launch stack

  Scenario: launch a new stack
    Given stack "A" does not exist
    and the template for stack "A" is valid
    When the user launches stack "A"
    Then stack "A" exists in "CREATE_COMPLETE" state

  Scenario: launch a stack that was newly created
    Given stack "A" exists in "CREATE_COMPLETE" state
    and the template for stack "A" is updated
    When the user launches stack "A"
    Then stack "A" exists in "UPDATE_COMPLETE" state

  Scenario: launch a stack that has been previously updated
    Given stack "A" exists in "UPDATE_COMPLETE" state
    and the template for stack "A" is valid
    When the user launches stack "A"
    Then stack "A" exists in "UPDATE_COMPLETE" state
