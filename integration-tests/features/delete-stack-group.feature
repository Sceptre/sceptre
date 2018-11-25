Feature: Delete stack_group

  Scenario: delete a stack_group that does not exist
    Given stack_group "1" does not exist
    When the user deletes stack_group "2"
    Then all the stacks in stack_group "2" do not exist

  Scenario: delete a stack_group that already exists
    Given all the stacks in stack_group "2" are in "CREATE_COMPLETE"
    When the user deletes stack_group "2"
    Then all the stacks in stack_group "2" do not exist

  Scenario: delete a stack_group that partially exists
    Given stack "2/A" exists in "CREATE_COMPLETE" state
    When the user deletes stack_group "2"
    Then all the stacks in stack_group "2" do not exist

  Scenario: delete a stack_group that already exists with ignore dependencies
    Given all the stacks in stack_group "2" are in "CREATE_COMPLETE"
    When the user deletes stack_group "2" with ignore dependencies
    Then all the stacks in stack_group "2" do not exist
