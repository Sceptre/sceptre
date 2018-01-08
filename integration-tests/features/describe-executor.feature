Feature: Describe executor

  Scenario: describe a executor that does not exist
    Given executor "2" does not exist
    When the user describes executor "2"
    Then all stacks in executor "2" are described as "PENDING"

  Scenario: describe a executor that already exists
    Given all the stacks in executor "2" are in "CREATE_COMPLETE"
    When the user describes executor "2"
    Then all stacks in executor "2" are described as "CREATE_COMPLETE"

  Scenario: describe a executor that partially exists
    Given stack "2/A" exists in "CREATE_COMPLETE" state
    and stack "2/B" exists in "UPDATE_COMPLETE" state
    and stack "2/C" does not exist
    When the user describes executor "2"
    Then stack "2/A" is described as "CREATE_COMPLETE"
    and stack "2/B" is described as "UPDATE_COMPLETE"
    and stack "2/C" is described as "PENDING"
