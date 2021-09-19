Feature: Execute change set

  Scenario: execute a change set that exists
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    And stack "1/A" has change set "A" using "updated_template.json"
    When the user executes change set "A" for stack "1/A"
    Then stack "1/A" does not have change set "A"
    And stack "1/A" was updated with change set "A"

  Scenario: execute a change set that does not exist
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    And stack "1/A" does not have change set "A"
    When the user executes change set "A" for stack "1/A"
    Then a "ClientError" is raised
    And the user is told "change set does not exist"

  Scenario: execute a change set that exists with ignore dependencies
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    And stack "1/A" has change set "A" using "updated_template.json"
    When the user executes change set "A" for stack "1/A" with ignore dependencies
    Then stack "1/A" does not have change set "A"
    And stack "1/A" was updated with change set "A"

  Scenario: execute a change set for SAM template with no changes
    Given stack "1/A" exists using "sam_template.yaml"
    And stack "1/A" has change set "A" using "sam_template.yaml"
    When the user executes change set "A" for stack "1/A"
    Then stack "1/A" does not have change set "A"
