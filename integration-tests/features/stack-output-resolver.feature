Feature: Stack output resolver

  @wip
  Scenario: launch a stack referencing an output of existing stack
    Given stack "6/1/A" exists using "output_template.json"
    and stack "6/1/B" does not exist
    and stack "6/1/C" does not exist
    When the user launches stack "6/1/B"
    Then stack "6/1/A" exists in "CREATE_COMPLETE" state

  @wip
  Scenario: launch a stack referencing an output of a non-existant stack
    Given stack "6/1/A" does not exist
    and stack "6/1/B" does not exist
    When the user launches stack "6/1/B"
    Then the user is told ""

  @wip
  Scenario: launch a environment where stacks reference other stack outputs
    Given environment "6/1" does not exist
    When the user launches environment "6/1"
    Then all the stacks in environment "6/1" are in "CREATE_COMPLETE"
    and that stack "6/1/A" was created before "6/1/B"
    and that stack "6/1/B" was created before "6/1/C"

  @wip
  Scenario: delete a stack referencing an output of existing stack
    Given stack "6/1/A" exists in "CREATE_COMPLETE" state
    and stack "6/1/B" exists in "CREATE_COMPLETE" state
    When the user deletes stack "6/1/B"
    Then stack "6/1/A" exists in "CREATE_COMPLETE" state
    and stack "6/1/B" does not exist

  @wip
  Scenario: delete a environment where stacks reference other stack outputs
    Given all the stacks in environment "6/1" are in "CREATE_COMPLETE"
    When the user deletes environment "6/1"
    Then all the stacks in environment "6/1" do not exist
