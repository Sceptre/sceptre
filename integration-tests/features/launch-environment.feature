Feature: Launch environment

  Scenario: launch a environment that does not exist
    Given environment "2" does not exist
    When the user launches environment "2"
    Then all the stacks in environment "2" are in "CREATE_COMPLETE"

  Scenario: launch a environment that already exists
    Given all the stacks in environment "2" are in "CREATE_COMPLETE"
    When the user launches environment "2"
    Then all the stacks in environment "2" are in "CREATE_COMPLETE"

  Scenario: launch a environment that partially exists
    Given stack "2/A" exists in "CREATE_COMPLETE" state
    When the user launches environment "2"
    Then all the stacks in environment "2" are in "CREATE_COMPLETE"

  Scenario: launch a environment with updates that partially exists
    Given stack "2/A" exists in "CREATE_COMPLETE" state
    and stack "2/B" does not exist
    and stack "2/C" does not exist
    and the template for stack "2/A" is updated_template.json
    When the user launches environment "2"
    Then stack "2/A" exists in "UPDATE_COMPLETE" state
    and stack "2/B" exists in "CREATE_COMPLETE" state
    and stack "2/C" exists in "CREATE_COMPLETE" state

  Scenario: launch a environment with updates that already exists
    Given all the stacks in environment "2" are in "CREATE_COMPLETE"
    and the template for stack "2/A" is updated_template.json
    and the template for stack "2/B" is updated_template.json
    and the template for stack "2/C" is updated_template.json
    When the user launches environment "2"
    Then all the stacks in environment "2" are in "UPDATE_COMPLETE"

  Scenario: launch a environment with nested environments that do not exist
    Given environment "5" does not exist
    When the user launches environment "5"
    Then all the stacks in environment "5" are in "CREATE_COMPLETE"
