Feature: Drift Detection
  Scenario: Detects no drift on a stack that with no drift
    Given stack "14/A" exists using "loggroup14.yaml"
    When the user detects drift on stack "14/A"
    Then stack drift status is "IN_SYNC"

  Scenario: Shows no drift on a stack that with no drift
    Given stack "14/A" exists using "loggroup14.yaml"
    When the user shows drift on stack "14/A"
    Then stack resource drift status is "IN_SYNC"

  Scenario: Detects drift on a stack has has drifted
    Given stack "14/A" exists using "loggroup14.yaml"
    And a stack setting in log group "IntegrationTest14" has drifted
    When the user detects drift on stack "14/A"
    Then stack drift status is "DRIFTED"

  Scenario: Shows drift on a stack has has drifted
    Given stack "14/A" exists using "loggroup14.yaml"
    And a stack setting in log group "IntegrationTest14" has drifted
    When the user shows drift on stack "14/A"
    Then stack resource drift status is "MODIFIED"

  Scenario: Detects drift on a stack group that partially exists
    Given stack "15/A" exists using "loggroup15.yaml"
    And stack "15/B" does not exist
    And a stack setting in log group "IntegrationTest15" has drifted
    When the user detects drift on stack_group "15"
    Then stack_group drift status is "STACK_DOES_NOT_EXIST" and "DRIFTED"

  Scenario: Does not blow up on a stack group that doesn't exist
    Given stack_group "15" does not exist
    When the user detects drift on stack_group "15"
    Then stack_group drift status is "STACK_DOES_NOT_EXIST" and "STACK_DOES_NOT_EXIST"
