Feature: Drift Detection
  Scenario: Detects no drift on a stack that with no drift
    Given stack "drift-single/A" exists using "loggroup.yaml"
    When the user detects drift on stack "drift-single/A"
    Then stack drift status is "IN_SYNC"

  Scenario: Shows no drift on a stack that with no drift
    Given stack "drift-single/A" exists using "loggroup.yaml"
    When the user shows drift on stack "drift-single/A"
    Then stack resource drift status is "IN_SYNC"

  Scenario: Detects drift on a stack has has drifted
    Given stack "drift-single/A" exists using "loggroup.yaml"
    And a stack setting in stack "drift-single/A" has drifted
    When the user detects drift on stack "drift-single/A"
    Then stack drift status is "DRIFTED"

  Scenario: Shows drift on a stack has has drifted
    Given stack "drift-single/A" exists using "loggroup.yaml"
    And a stack setting in stack "drift-single/A" has drifted
    When the user shows drift on stack "drift-single/A"
    Then stack resource drift status is "MODIFIED"

  Scenario: Detects drift on a stack group that partially exists
    Given stack "drift-group/A" exists using "loggroup.yaml"
    And stack "drift-group/B" does not exist
    And a stack setting in stack "drift-group/A" has drifted
    When the user detects drift on stack_group "drift-group"
    Then stack_group drift statuses are each one of "DRIFTED,STACK_DOES_NOT_EXIST"

  Scenario: Does not blow up on a stack group that doesn't exist
    Given stack_group "drift-group" does not exist
    When the user detects drift on stack_group "drift-group"
    Then stack_group drift statuses are each one of "STACK_DOES_NOT_EXIST,STACK_DOES_NOT_EXIST"
