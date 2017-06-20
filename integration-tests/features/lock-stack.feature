Feature: Lock stack

  Scenario: lock a stack that exists without a stack policy
    Given stack "A" exists in "CREATE_COMPLETE" state
    and the policy for stack "A" is not set
    When the user locks stack "A"
    Then the stack policy is deny all

  Scenario: lock a stack that exists with a stack policy
    Given stack "A" exists in "CREATE_COMPLETE" state
    and the policy for stack "A" is allow all
    When the user locks stack "A"
    Then the policy for stack "A" is deny all

  Scenario: lock a stack that does not exist
    Given stack "A" does not exist
    When the user locks stack "A"
    Then the user is told stack does not exist
