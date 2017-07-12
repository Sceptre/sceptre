Feature: Stack output external resolver

  @wip
  Scenario: launch a stack referencing an output of existing stack
    Given stack "6/2/A" does not exist
    and stack "6/2/B" exists in "CREATE_COMPLETE" state
    When the user launches stack "6/2/A"
    Then stack "6/2/A" exists in "CREATE_COMPLETE" state

  @wip
  Scenario: launch a stack referencing an output of a non-existant stack
    Given stack "6/2/A" does not exist
    and stack "6/1/B" does not exist
    When the user launches stack "6/1/A"
    Then a "StackDoesNotExistError" is raised

  @wip
  Scenario: delete a stack referencing an output of existing stack
    Given stack "6/2/B" exists in "CREATE_COMPLETE" state
    and stack "6/2/A" exists in "CREATE_COMPLETE" state
    When the user deletes stack "6/2/A"
    Then stack "6/2/A" does not exist
