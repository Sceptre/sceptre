Feature: List change sets

  @now
  Scenario: list change sets on existing stack with change sets
    Given stack "A" exists in "CREATE_COMPLETE" state
    and stack "A" has change set "A" using updated_template.json
    When the user lists change sets for stack "A"
    Then the change sets for stack "A" are listed


  @now
  Scenario: list change sets on existing stack with no change sets
    Given stack "A" exists in "CREATE_COMPLETE" state
    and stack "A" has no change sets
    When the user lists change sets for stack "A"
    Then no change sets for stack "A" are listed
