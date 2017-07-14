Feature: Unlock stack

  Scenario: unlock a stack that exists with a stack policy
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and the policy for stack "1/A" is deny all
    When the user unlocks stack "1/A"
    Then the policy for stack "1/A" is allow all

  Scenario: unlock a stack that does not exist
    Given stack "1/A" does not exist
    When the user unlocks stack "1/A"
    Then a "ClientError" is raised
    and the user is told "stack does not exist"
