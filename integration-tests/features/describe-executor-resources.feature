Feature: Describe executor resources

  Scenario: describe resources of an executor that does not exist
    Given executor "2" does not exist
    When the user describes resources in executor "2"
    Then no resources are described

  Scenario: describe rosources of an executor that already exists
    Given all the stacks in executor "2" are in "CREATE_COMPLETE"
    When the user describes resources in executor "2"
    Then only all resources in executor "2" are described

  Scenario: describe a executor that partially exists
    Given stack "2/A" exists in "CREATE_COMPLETE" state
    and stack "2/B" does not exist
    and stack "2/C" does not exist
    When the user describes resources in executor "2"
    Then only resources in stack "2/A" are described
