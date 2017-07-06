Feature: Update stack

  @now
  Scenario: update a stack that was newly created
    Given stack "A" exists in "CREATE_COMPLETE" state
    and the template for stack "A" is updated_template.json
    When the user updates stack "A"
    Then stack "A" exists in "UPDATE_COMPLETE" state

  @now
  Scenario: update a stack that has been previously updated
    Given stack "A" exists in "UPDATE_COMPLETE" state
    and the template for stack "A" is updated_template.json
    When the user updates stack "A"
    Then stack "A" exists in "UPDATE_COMPLETE" state

  @now
  Scenario: update a stack that does not exists
    Given stack "A" does not exist
    and the template for stack "A" is updated_template.json
    When the user updates stack "A"
    Then stack "A" does not exist
