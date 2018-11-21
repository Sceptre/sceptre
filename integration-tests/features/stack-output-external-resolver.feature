Feature: Stack output external resolver

  Scenario: launch a stack referencing the external output of an existing stack
    Given stack_group "9" has AWS config "aws-config" set
    and stack "9/A" exists using "dependencies/independent_template.json"
    and stack "9/B" does not exist
    When the user launches stack "9/B"
    Then stack "9/B" exists in "CREATE_COMPLETE" state
