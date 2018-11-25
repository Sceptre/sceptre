Feature: Describe-stack-resources

  Scenario: describe the resources of a stack that exists
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    When the user describes the resources of stack "1/A"
    Then the resources of stack "1/A" are described

  Scenario: describe the resources of a stack that exists with ignore dependencies
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    When the user describes the resources of stack "1/A" with ignore dependencies
    Then the resources of stack "1/A" are described
