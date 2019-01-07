Feature: Create change set

  Scenario: create new change set with updated template
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and the template for stack "1/A" is "updated_template.json"
    and stack "1/A" does not have change set "A"
    When the user creates change set "A" for stack "1/A"
    Then stack "1/A" has change set "A" in "CREATE_COMPLETE" state

  Scenario: create new change set with same template
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and the template for stack "1/A" is "valid_template.json"
    and stack "1/A" does not have change set "A"
    When the user creates change set "A" for stack "1/A"
    Then stack "1/A" has change set "A" in "FAILED" state

  Scenario: create new change set with stack that does not exist
    Given stack "1/A" does not exist
    and the template for stack "1/A" is "valid_template.json"
    When the user creates change set "A" for stack "1/A"
    Then a "ClientError" is raised
    and the user is told "stack does not exist"

  Scenario: create new change set with updated template and ignore dependencies
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and the template for stack "1/A" is "updated_template.json"
    and stack "1/A" does not have change set "A"
    When the user creates change set "A" for stack "1/A" with ignore dependencies
    Then stack "1/A" has change set "A" in "CREATE_COMPLETE" state

  Scenario: create new change set with a SAM template
    Given stack "11/A" exists in "CREATE_COMPLETE" state
    and the template for stack "11/A" is "sam_updated_template.yaml"
    and stack "11/A" does not have change set "A"
    When the user creates change set "A" for stack "11/A"
    Then stack "11/A" has change set "A" in "CREATE_COMPLETE" state
