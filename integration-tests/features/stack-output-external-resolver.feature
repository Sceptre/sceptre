Feature: Stack output external resolver

  Scenario: launch a stack referencing an output of existing stack
    Given stack "6/2/B" does not exist
    and external stack "6/2/A" exists using "dependencies/independent_template.json"
    When the user launches stack "6/2/B"
    Then stack "6/2/B" exists in "CREATE_COMPLETE" state

  Scenario: launch a stack referencing an output of a non-existant stack
    Given stack "6/2/A" does not exist
    and stack "6/2/B" does not exist
    When the user launches stack "6/2/B"
    Then a "StackDoesNotExistError" is raised

  Scenario: delete a stack referencing an output of existing stack
    Given stack "6/2/A" exists in "CREATE_COMPLETE" state
    and stack "6/2/B" exists in "CREATE_COMPLETE" state
    When the user deletes stack "6/2/B"
    Then stack "6/2/B" does not exist
