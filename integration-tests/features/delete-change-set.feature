Feature: Delete change set

  @now
  Scenario: delete a change set that exists
    Given stack "A" exists in "CREATE_COMPLETE" state
    and stack "A" has change set "A" using updated_template.json
    When the user deletes change set "A" for stack "A"
    Then stack "A" does not have change set "A"

  # @wip
  # Scenario: delete a change set that does not exist
  #   Given stack "A" exists in "CREATE_COMPLETE" state
  #   and stack "A" does not have change set "A"
  #   When the user deletes change set "A" for stack "A"
  #   Then the user is told the change set does not exist
