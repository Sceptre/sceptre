Feature: Describe environment resources

  Scenario: describe resources of an environment that does not exist
    Given environment "2" does not exist
    When the user describes resources in environment "2"
    Then no resources are described

  Scenario: describe rosources of an environment that already exists
    Given all the stacks in environment "2" are in "CREATE_COMPLETE"
    When the user describes resources in environment "2"
    Then only all resources in environment "2" are described

  Scenario: describe a environment that partially exists
    Given stack "2/A" exists in "CREATE_COMPLETE" state
    and stack "2/B" does not exist
    and stack "2/C" does not exist
    When the user describes resources in environment "2"
    Then only resources in stack "2/A" are described
