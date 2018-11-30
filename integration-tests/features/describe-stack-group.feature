Feature: Describe stack_group

  Scenario: describe a stack_group that does not exist
    Given stack_group "2" does not exist
    When the user describes stack_group "2"
    Then no resources are described

  Scenario: describe a stack_group that already exists
    Given all the stacks in stack_group "2" are in "CREATE_COMPLETE"
    When the user describes stack_group "2"
    Then all stacks in stack_group "2" are described as "CREATE_COMPLETE"

  Scenario: describe a stack_group that partially exists
    Given stack "2/A" exists in "CREATE_COMPLETE" state
    and stack "2/B" exists in "UPDATE_COMPLETE" state
    and stack "2/C" does not exist
    When the user describes stack_group "2"
    Then stack "2/A" is described as "CREATE_COMPLETE"
    and stack "2/B" is described as "UPDATE_COMPLETE"
    and stack "2/C" is described as "PENDING"

  Scenario: describe a stack_group that already exists with ignore dependencies
    Given all the stacks in stack_group "2" are in "CREATE_COMPLETE"
    When the user describes stack_group "2" with ignore dependencies
    Then all stacks in stack_group "2" are described as "CREATE_COMPLETE"

