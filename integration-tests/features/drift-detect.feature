Feature: Drift Detect
  Scenario: Detects drift on a stack that with drift
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    And the template for stack "1/A" is "loggroup.yaml"
    And a stack setting in stack "1/A" has drifted
    When the user detects drift on stack "1/A"
    Then drift is detected
