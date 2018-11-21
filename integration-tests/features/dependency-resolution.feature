Feature: Dependency resolution

  Scenario: launch a stack_group with dependencies that is partially complete
    Given stack "3/A" exists in "CREATE_COMPLETE" state
    and stack "3/B" exists in "CREATE_COMPLETE" state
    and stack "3/C" does not exist
    When the user launches stack_group "3"
    Then all the stacks in stack_group "3" are in "CREATE_COMPLETE"
    and that stack "3/A" was created before "3/B"
    and that stack "3/B" was created before "3/C"

  Scenario: delete a stack_group with dependencies that is partially complete
    Given stack "3/A" exists in "CREATE_COMPLETE" state
    and stack "3/B" exists in "CREATE_COMPLETE" state
    and stack "3/C" does not exist
    When the user deletes stack_group "3"
    Then all the stacks in stack_group "3" do not exist

  Scenario: delete a stack_group with dependencies
    Given all the stacks in stack_group "3" are in "CREATE_COMPLETE"
    When the user deletes stack_group "3"
    Then all the stacks in stack_group "3" do not exist
