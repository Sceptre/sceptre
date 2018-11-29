Feature: Launch stack_group

  Scenario: launch a stack_group that does not exist
    Given stack_group "2" does not exist
    When the user launches stack_group "2"
    Then all the stacks in stack_group "2" are in "CREATE_COMPLETE"
  
  Scenario: launch a stack_group, excluding dependencies, that does not exist
    Given stack_group "2" does not exist
    When the user launches stack_group "2"
    Then all the stacks in stack_group "2" are in "CREATE_COMPLETE"

  Scenario: launch a stack_group that already exists
    Given all the stacks in stack_group "2" are in "CREATE_COMPLETE"
    When the user launches stack_group "2"
    Then all the stacks in stack_group "2" are in "CREATE_COMPLETE"

  Scenario: launch a stack_group that partially exists
    Given stack "2/A" exists in "CREATE_COMPLETE" state
    When the user launches stack_group "2"
    Then all the stacks in stack_group "2" are in "CREATE_COMPLETE"

  Scenario: launch a stack_group with updates that partially exists
    Given stack "2/A" exists in "CREATE_COMPLETE" state
    and stack "2/B" does not exist
    and stack "2/C" does not exist
    and the template for stack "2/A" is "updated_template.json"
    When the user launches stack_group "2"
    Then stack "2/A" exists in "UPDATE_COMPLETE" state
    and stack "2/B" exists in "CREATE_COMPLETE" state
    and stack "2/C" exists in "CREATE_COMPLETE" state

  Scenario: launch a stack_group with updates that already exists
    Given all the stacks in stack_group "2" are in "CREATE_COMPLETE"
    and the template for stack "2/A" is "updated_template.json"
    and the template for stack "2/B" is "updated_template.json"
    and the template for stack "2/C" is "updated_template.json"
    When the user launches stack_group "2"
    Then all the stacks in stack_group "2" are in "UPDATE_COMPLETE"

  Scenario: launch a stack_group with nested stack_groups that do not exist
    Given stack_group "5" does not exist
    When the user launches stack_group "5"
    Then all the stacks in stack_group "5" are in "CREATE_COMPLETE"

  Scenario: launch a stack_group that does not exist ignoring dependencies
    Given stack_group "2" does not exist
    When the user launches stack_group "2" with ignore dependencies
    Then all the stacks in stack_group "2" are in "CREATE_COMPLETE"
