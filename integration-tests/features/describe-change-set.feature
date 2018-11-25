Feature: Describe change sets

  Scenario: describe a change set that exists
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and stack "1/A" has change set "A" using "updated_template.json"
    When the user describes change set "A" for stack "1/A"
    Then change set "A" for stack "1/A" is described

  Scenario: describe a change set that does not exist
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and stack "1/A" has no change sets
    When the user describes change set "A" for stack "1/A"
    Then a "ClientError" is raised
    and the user is told "change set does not exist"

  Scenario: describe a change set that exists with ignore dependencies
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and stack "1/A" has change set "A" using "updated_template.json"
    When the user describes change set "A" for stack "1/A" with ignore dependencies
    Then change set "A" for stack "1/A" is described


