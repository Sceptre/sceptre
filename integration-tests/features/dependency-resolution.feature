Feature: Dependency resolution

  Scenario: launch an environment with dependencies
    Given environment "3" does not exist
    When the user launches environment "3"
    Then all the stacks in environment "3" are in "CREATE_COMPLETE"
    and that stack "3/A" was created before "3/B"
    and that stack "3/B" was created before "3/C"

  Scenario: launch an environment with dependencies that is partially complete
    Given stack "3/A" exists in "CREATE_COMPLETE" state
    and stack "3/B" exists in "CREATE_COMPLETE" state
    and stack "3/C" does not exist
    When the user launches environment "3"
    Then all the stacks in environment "3" are in "CREATE_COMPLETE"
    and that stack "3/A" was created before "3/B"
    and that stack "3/B" was created before "3/C"

  Scenario: delete an environment with dependencies that is partially complete
    Given stack "3/A" exists in "CREATE_COMPLETE" state
    and stack "3/B" exists in "CREATE_COMPLETE" state
    and stack "3/C" does not exist
    When the user deletes environment "3"
    Then all the stacks in environment "3" do not exist

  Scenario: delete an environment with dependencies
    Given all the stacks in environment "3" are in "CREATE_COMPLETE"
    When the user deletes environment "3"
    Then all the stacks in environment "3" do not exist
