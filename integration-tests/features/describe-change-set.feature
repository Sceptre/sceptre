Feature: Describe change sets

  @wip
  Scenario: describe a change set that exists
    Given stack "A" exists in "CREATE_COMPLETE" state
    and stack "A" has change set "A" using updated_template.json
    When the user describes change set "A" for stack "A"
    Then change set "A" for stack "A" is described


  @wip
  Scenario: describe a change set that does not exist
    Given stack "A" exists in "CREATE_COMPLETE" state
    and stack "A" has no change sets
    When the user describes change set "A" for stack "A"
    Then the user is told the change set does not exist
