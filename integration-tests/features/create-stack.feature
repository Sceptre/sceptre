Feature: Create stack

  Scenario: create new stack
    Given stack "1/A" does not exist
    and the template for stack "1/A" is "valid_template.json"
    When the user creates stack "1/A"
    Then stack "1/A" exists in "CREATE_COMPLETE" state

  Scenario: create a stack that already exists
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and the template for stack "1/A" is "valid_template.json"
    When the user creates stack "1/A"
    Then stack "1/A" exists in "CREATE_COMPLETE" state

  Scenario: create new stack that has previously failed
    Given stack "1/A" exists in "CREATE_FAILED" state
    and the template for stack "1/A" is "valid_template.json"
    When the user creates stack "1/A"
    Then stack "1/A" exists in "CREATE_FAILED" state

  Scenario: create new stack that is rolled back on failure
    Given stack "8/A" does not exist
    and the template for stack "8/A" is "invalid_template.json"
    When the user creates stack "8/A"
    Then stack "8/A" exists in "ROLLBACK_COMPLETE" state

  Scenario: create new stack that is retained on failure
    Given stack "8/B" does not exist
    and the template for stack "8/B" is "invalid_template.json"
    When the user creates stack "8/B"
    Then stack "8/B" exists in "CREATE_FAILED" state
