Feature: Launch stack

  Scenario: launch a new stack
    Given stack "1/A" does not exist
    And the template for stack "1/A" is "valid_template.json"
    When the user launches stack "1/A"
    Then stack "1/A" exists in "CREATE_COMPLETE" state

  Scenario: launch a stack that was newly created
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    And the template for stack "1/A" is "updated_template.json"
    When the user launches stack "1/A"
    Then stack "1/A" exists in "UPDATE_COMPLETE" state

  Scenario: launch a stack that has been previously updated
    Given stack "1/A" exists in "UPDATE_COMPLETE" state
    And the template for stack "1/A" is "valid_template.json"
    When the user launches stack "1/A"
    Then stack "1/A" exists in "UPDATE_COMPLETE" state

  Scenario: launch a new stack with ignore dependencies
    Given stack "1/A" does not exist
    And the template for stack "1/A" is "valid_template.json"
    When the user launches stack "1/A" with ignore dependencies
    Then stack "1/A" exists in "CREATE_COMPLETE" state

  Scenario: launch an obsolete that doesn't exist
    Given stack "launch-actions/obsolete" does not exist
    When the user launches stack "launch-actions/obsolete"
    Then stack "launch-actions/obsolete" does not exist

  Scenario: launch an obsolete stack that does exist without --prune
    Given stack "launch-actions/obsolete" exists using "valid_template.json"
    When the user launches stack "launch-actions/obsolete"
    Then stack "launch-actions/obsolete" exists in "CREATE_COMPLETE" state

  Scenario: launch an obsolete stack that does exist with --prune
    Given stack "launch-actions/obsolete" exists using "valid_template.json"
    When the user launches stack "launch-actions/obsolete" with --prune
    Then stack "launch-actions/obsolete" does not exist

  Scenario: launch an ignored stack that doesn't exist
    Given stack "launch-actions/ignore" does not exist
    When the user launches stack "launch-actions/ignore"
    Then stack "launch-actions/ignore" does not exist

  Scenario: launch an ignored stack that does exist
    Given stack "launch-actions/ignore" exists using "valid_template.json"
    When the user launches stack "launch-actions/ignore"
    Then stack "launch-actions/ignore" exists in "CREATE_COMPLETE" state
