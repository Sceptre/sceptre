Feature: Delete change set

  Scenario: delete a change set that exists
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and stack "1/A" has change set "A" using "updated_template.json"
    When the user deletes change set "A" for stack "1/A"
    Then stack "1/A" does not have change set "A"
      

  Scenario: delete a change set that exists with ignore dependencies
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and stack "1/A" has change set "A" using "updated_template.json"
    When the user deletes change set "A" for stack "1/A" with ignore dependencies
    Then stack "1/A" does not have change set "A"

  # @wip
  # Scenario: delete a change set that does not exist
  #   Given stack "1/A" exists in "CREATE_COMPLETE" state
  #   and stack "1/A" does not have change set "1/A"
  #   When the user deletes change set "1/A" for stack "1/A"
  #   Then the user is told the change set does not exist
