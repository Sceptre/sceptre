Feature: Prune

  Scenario: Prune with no stacks marked obsolete does nothing
    Given stack "pruning/not-obsolete" exists using "valid_template.json"
    When command path "pruning/not-obsolete" is pruned
    Then stack "pruning/not-obsolete" exists in "CREATE_COMPLETE" state

  Scenario: Prune whole project deletes all obsolete stacks that exist
    Given all the stacks in stack_group "pruning" are in "CREATE_COMPLETE"
    And stack "launch-actions/obsolete" exists using "valid_template.json"
    When the whole project is pruned
    Then stack "pruning/obsolete-1" does not exist
    And stack "pruning/obsolete-2" does not exist
    And stack "launch-actions/obsolete" does not exist
    And stack "pruning/not-obsolete" exists in "CREATE_COMPLETE" state

  Scenario: Prune command path only deletes stacks on command path
    Given stack "pruning/obsolete-1" exists using "valid_template.json"
    And stack "pruning/obsolete-2" exists using "valid_template.json"
    When command path "pruning/obsolete-1.yaml" is pruned
    Then stack "pruning/obsolete-1" does not exist
    And stack "pruning/obsolete-2" exists in "CREATE_COMPLETE" state
