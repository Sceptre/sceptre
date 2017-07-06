Feature: Create change set

  @now
  Scenario: create new change set with updated template
    Given stack "A" exists in "CREATE_COMPLETE" state
    and the template for stack "A" is updated_template.json
    and stack "A" does not have change set "A"
    When the user creates change set "A" for stack "A"
    Then stack "A" has change set "A" in "CREATE_COMPLETE" state

  @now
  Scenario: create new change set with same template
    Given stack "A" exists in "CREATE_COMPLETE" state
    and the template for stack "A" is valid_template.json
    and stack "A" does not have change set "A"
    When the user creates change set "A" for stack "A"
    Then stack "A" has change set "A" in "FAILED" state

  @now
  Scenario: create new change set with stack that does not exist
    Given stack "A" does not exist
    When the user creates change set "A" for stack "A"
    Then the user is told the stack does not exist
