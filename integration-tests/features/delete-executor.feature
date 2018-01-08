Feature: Delete executor

  Scenario: delete an executor that does not exist
    Given executor "1" does not exist
    When the user deletes executor "2"
    Then all the stacks in executor "2" do not exist

  Scenario: delete an executor that already exists
    Given all the stacks in executor "2" are in "CREATE_COMPLETE"
    When the user deletes executor "2"
    Then all the stacks in executor "2" do not exist

  Scenario: delete an executor that partially exists
    Given stack "2/A" exists in "CREATE_COMPLETE" state
    When the user deletes executor "2"
    Then all the stacks in executor "2" do not exist
