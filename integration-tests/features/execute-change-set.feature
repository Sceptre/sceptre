Feature: Execute change set

  @now
  Scenario: execute a change set that exists
    Given stack "A" exists in "CREATE_COMPLETE" state
    and stack "A" has change set "A" using updated_template.json
    When the user executes change set "A" for stack "A"
    Then stack "A" does not have change set "A"
    and stack "A" was updated with change set "A"

  @now
  Scenario: execute a change set that does not exist
    Given stack "A" exists in "CREATE_COMPLETE" state
    and stack "A" does not have change set "A"
    When the user executes change set "A" for stack "A"
    Then the user is told the change set does not exist
