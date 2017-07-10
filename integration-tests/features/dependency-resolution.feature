Feature: Dependency resolution

  Scenario: launch a environment with dependencies
    Given environment "3" does not exist
    When the user launches environment "3"
    Then all the stacks in environment "3" are in "CREATE_COMPLETE"
    and that stack "3/A" was created before "3/B"
    and that stack "3/B" was created before "3/C"

  Scenario: launch a environment with dependencies that is partially complete
    Given stack "3/A" exists in "CREATE_COMPLETE" state
    and stack "3/B" exists in "CREATE_COMPLETE" state
    and stack "3/C" does not exist
    When the user launches environment "3"
    Then all the stacks in environment "3" are in "CREATE_COMPLETE"
    and that stack "3/A" was created before "3/B"
    and that stack "3/B" was created before "3/C"

  # Need to fix bug to pass the scenario
  # @wip
  # Scenario: launch a environment with dependencies outside the same environment
  #   Given environment "4" does not exist
  #   and stack "3/A" does not exist
  #   When the user launches environment "4"
  #   Then stack "4/A" exists in "CREATE_COMPLETE" state
  #   and stack "4/B" exists in "CREATE_COMPLETE" state
  #   and stack "4/C" does not exist

  Scenario: delete a environment with dependencies that is partially complete
    Given stack "3/A" exists in "CREATE_COMPLETE" state
    and stack "3/B" exists in "CREATE_COMPLETE" state
    and stack "3/C" does not exist
    When the user deletes environment "3"
    Then all the stacks in environment "3" do not exist

  Scenario: delete a environment with dependencies
    Given all the stacks in environment "3" are in "CREATE_COMPLETE"
    When the user deletes environment "3"
    Then all the stacks in environment "3" do not exist
