Feature: List change sets

  Scenario: list change sets on existing stack with change sets
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and stack "1/A" has change set "A" using "updated_template.json"
    When the user lists change sets for stack "1/A"
    Then the change sets for stack "1/A" are listed

  Scenario: list change sets on existing stack with no change sets
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and stack "1/A" has no change sets
    When the user lists change sets for stack "1/A"
    Then no change sets for stack "1/A" are listed

  Scenario: list change sets on existing stack with change sets with ignore dependencies
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and stack "1/A" has change set "A" using "updated_template.json"
    When the user lists change sets for stack "1/A" with ignore dependencies
    Then the change sets for stack "1/A" are listed


