Feature: Create change set

  Scenario: create new change set with updated template
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and the template for stack "1/A" is updated_template.json
    and stack "1/A" does not have change set "A"
    When the user creates change set "A" for stack "1/A"
    Then stack "1/A" has change set "A" in "CREATE_COMPLETE" state

  Scenario: create new change set with same template
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and the template for stack "1/A" is valid_template.json
    and stack "1/A" does not have change set "A"
    When the user creates change set "A" for stack "1/A"
    Then stack "1/A" has change set "A" in "FAILED" state

  Scenario: create new change set with stack that does not exist
    Given stack "1/A" does not exist
    When the user creates change set "A" for stack "1/A"
    Then the user is told the stack does not exist
