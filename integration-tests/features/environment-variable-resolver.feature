Feature: Environment variable resolver

  @wip
  Scenario: launch a stack referencing a set environment variable
    Given stack "6/2/A" does not exist
    and environment variable "SCEPTRE_CI_VAR" is "some_value"
    When the user launches stack "6/2/A"
    Then stack "6/2/A" exists in "CREATE_COMPLETE" state

  @wip
  Scenario: launch a stack referencing a unset environment variable
    Given stack "6/2/A" does not exist
    and environment variable "SCEPTRE_CI_VAR" is not set
    When the user launches stack "6/2/A"
    Then stack "6/2/A" exists in "CREATE_COMPLETE" state
