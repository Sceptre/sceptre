Feature: Launch stack

  Scenario: launch a new stack
    Given stack "1/A" does not exist
    and the template for stack "1/A" is "valid_template.json"
    When the user launches stack "1/A"
    Then stack "1/A" exists in "CREATE_COMPLETE" state

  Scenario: launch a stack that was newly created
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and the template for stack "1/A" is "updated_template.json"
    When the user launches stack "1/A"
    Then stack "1/A" exists in "UPDATE_COMPLETE" state

  Scenario: launch a stack that has been previously updated
    Given stack "1/A" exists in "UPDATE_COMPLETE" state
    and the template for stack "1/A" is "valid_template.json"
    When the user launches stack "1/A"
    Then stack "1/A" exists in "UPDATE_COMPLETE" state

  Scenario: launch a new stack with ignore dependencies
    Given stack "1/A" does not exist
    and the template for stack "1/A" is "valid_template.json"
    When the user launches stack "1/A" with ignore dependencies
    Then stack "1/A" exists in "CREATE_COMPLETE" state

