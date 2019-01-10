Feature: Update stack

  Scenario: update a stack that was newly created
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and the template for stack "1/A" is "updated_template.json"
    When the user updates stack "1/A"
    Then stack "1/A" exists in "UPDATE_COMPLETE" state

  Scenario: update a stack that has been previously updated
    Given stack "1/A" exists in "UPDATE_COMPLETE" state
    and the template for stack "1/A" is "updated_template.json"
    When the user updates stack "1/A"
    Then stack "1/A" exists in "UPDATE_COMPLETE" state

  Scenario: update a stack that does not exists
    Given stack "1/A" does not exist
    and the template for stack "1/A" is "updated_template.json"
    When the user updates stack "1/A"
    Then stack "1/A" does not exist

  Scenario: update a stack that is rolled back after timeout
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and the template for stack "1/A" is "updated_template_wait_300.json"
    and the stack_timeout for stack "1/A" is "1"
    When the user updates stack "1/A"
    Then stack "1/A" exists in "UPDATE_ROLLBACK_COMPLETE" state

  Scenario: update a stack that was newly created with ignore dependencies
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and the template for stack "1/A" is "updated_template.json"
    When the user updates stack "1/A" with ignore dependencies
    Then stack "1/A" exists in "UPDATE_COMPLETE" state

  Scenario: update a stack that was newly created with a SAM template
    Given stack "11/A" exists in "CREATE_COMPLETE" state
    and the template for stack "11/A" is "sam_updated_template.yaml"
    When the user updates stack "11/A"
    Then stack "11/A" exists in "UPDATE_COMPLETE" state