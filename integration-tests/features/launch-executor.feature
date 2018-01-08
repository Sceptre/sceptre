Feature: Launch executor

  Scenario: launch an executor that does not exist
    Given executor "2" does not exist
    When the user launches executor "2"
    Then all the stacks in executor "2" are in "CREATE_COMPLETE"

  Scenario: launch an executor that already exists
    Given all the stacks in executor "2" are in "CREATE_COMPLETE"
    When the user launches executor "2"
    Then all the stacks in executor "2" are in "CREATE_COMPLETE"

  Scenario: launch an executor that partially exists
    Given stack "2/A" exists in "CREATE_COMPLETE" state
    When the user launches executor "2"
    Then all the stacks in executor "2" are in "CREATE_COMPLETE"

  Scenario: launch an executor with updates that partially exists
    Given stack "2/A" exists in "CREATE_COMPLETE" state
    and stack "2/B" does not exist
    and stack "2/C" does not exist
    and the template for stack "2/A" is "updated_template.json"
    When the user launches executor "2"
    Then stack "2/A" exists in "UPDATE_COMPLETE" state
    and stack "2/B" exists in "CREATE_COMPLETE" state
    and stack "2/C" exists in "CREATE_COMPLETE" state

  Scenario: launch an executor with updates that already exists
    Given all the stacks in executor "2" are in "CREATE_COMPLETE"
    and the template for stack "2/A" is "updated_template.json"
    and the template for stack "2/B" is "updated_template.json"
    and the template for stack "2/C" is "updated_template.json"
    When the user launches executor "2"
    Then all the stacks in executor "2" are in "UPDATE_COMPLETE"

  Scenario: launch an executor with nested executors that do not exist
    Given executor "5" does not exist
    When the user launches executor "5"
    Then all the stacks in executor "5" are in "CREATE_COMPLETE"
