Feature: Stack output resolver

  Scenario: launch a stack referencing an output of existing stack
    Given stack "6/1/A" exists using "dependencies/independent_template.json"
    and stack "6/1/B" does not exist
    and stack "6/1/C" does not exist
    When the user launches stack "6/1/B"
    Then stack "6/1/B" exists in "CREATE_COMPLETE" state

  Scenario: launch a stack referencing an output of a non-existant stack
    Given stack "6/1/B" does not exist
    and stack "6/1/A" does not exist
    When the user launches stack "6/1/B"
    Then a "StackDoesNotExistError" is raised

  Scenario: launch a environment where stacks reference other stack outputs
    Given environment "6/1" does not exist
    When the user launches environment "6/1"
    Then all the stacks in environment "6/1" are in "CREATE_COMPLETE"
    and that stack "6/1/A" was created before "6/1/B"
    and that stack "6/1/B" was created before "6/1/C"

  Scenario: launch a environment where stacks are in different regions
    Given stack "6/2/A" does not exist in "eu-west-1"
    and stack "6/2/B" does not exist in "eu-west-2"
    and stack "6/2/C" does not exist in "eu-west-3"
    When the user launches environment "6/2"
    Then stack "6/2/A" in "eu-west-1" exists in "CREATE_COMPLETE" state
    and stack "6/2/B" in "eu-west-2" exists in "CREATE_COMPLETE" state
    and stack "6/2/C" in "eu-west-3" exists in "CREATE_COMPLETE" state

  Scenario: delete a stack referencing an output of existing stack
    Given stack "6/1/A" exists in "CREATE_COMPLETE" state
    and stack "6/1/B" exists in "CREATE_COMPLETE" state
    and stack "6/1/C" does not exist
    When the user deletes stack "6/1/B"
    Then stack "6/1/A" exists in "CREATE_COMPLETE" state
    and stack "6/1/B" does not exist

  Scenario: delete a stack referencing an output of existing stack
    Given stack "6/1/A" exists in "CREATE_COMPLETE" state
    and stack "6/1/B" exists in "CREATE_COMPLETE" state
    and stack "6/1/C" exists in "CREATE_COMPLETE" state
    When the user deletes environment "6/1"
    Then all the stacks in environment "6/1" do not exist
