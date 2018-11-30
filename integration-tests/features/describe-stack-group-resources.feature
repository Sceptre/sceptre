Feature: Describe stack_group resources

  Scenario: describe resources of a stack_group that does not exist
    Given stack_group "2" does not exist
    When the user describes resources in stack_group "2"
    Then no resources are described

  Scenario: describe resources of a stack_group that already exists
    Given all the stacks in stack_group "2" are in "CREATE_COMPLETE"
    When the user describes resources in stack_group "2"
    Then only all resources in stack_group "2" are described

  Scenario: describe a stack_group that partially exists
    Given stack "2/A" exists in "CREATE_COMPLETE" state
    and stack "2/B" does not exist
    and stack "2/C" does not exist
    When the user describes resources in stack_group "2"
    Then only resources in stack "2/A" are described

  Scenario: describe resources of a stack_group that already exists with ignore dependencies
    Given all the stacks in stack_group "2" are in "CREATE_COMPLETE"
    When the user describes resources in stack_group "2" with ignore dependencies
    Then only all resources in stack_group "2" are described

