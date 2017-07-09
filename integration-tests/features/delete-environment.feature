Feature: Delete environment

  Scenario: delete a environment that does not exist
    Given environment "1" does not exist
    When the user deletes environment "2"
    Then all the stacks in environment "2" do not exist

  Scenario: delete a environment that already exists
    Given all the stacks in environment "2" are in "CREATE_COMPLETE"
    When the user deletes environment "2"
    Then all the stacks in environment "2" do not exist

  Scenario: delete a environment that partially exists
    Given stack "2/A" exists in "CREATE_COMPLETE" state
    When the user deletes environment "2"
    Then all the stacks in environment "2" do not exist
