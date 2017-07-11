Feature: Create stack

  Scenario: create new stack
    Given stack "1/A" does not exist
    and the template for stack "1/A" is valid_template.json
    When the user creates stack "1/A"
    Then stack "1/A" exists in "CREATE_COMPLETE" state

  Scenario: create a stack that already exists
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and the template for stack "1/A" is valid_template.json
    When the user creates stack "1/A"
    Then stack "1/A" exists in "CREATE_COMPLETE" state

  Scenario: create new stack that has previously failed
    Given stack "1/A" exists in "CREATE_FAILED" state
    and the template for stack "1/A" is valid_template.json
    When the user creates stack "1/A"
    Then stack "1/A" exists in "CREATE_FAILED" state
