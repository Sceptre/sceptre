Feature: Update stack

  Scenario: update a stack that was newly created
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and the template for stack "1/A" is "updated_template.json"
    When the user updates stack "1/A"
    Then stack "1/A" exists in "UPDATE_COMPLETE" state

  Scenario: update a stack that has been previously updated
    Given stack "1/A" exists in "UPDATE_COMPLETE" state
    and the template for stack "1/A" is "updated_template.json"
    When the user updates stack "1/A"
    Then stack "1/A" exists in "UPDATE_COMPLETE" state

  Scenario: update a stack that does not exists
    Given stack "1/A" does not exist
    and the template for stack "1/A" is "updated_template.json"
    When the user updates stack "1/A"
    Then stack "1/A" does not exist
