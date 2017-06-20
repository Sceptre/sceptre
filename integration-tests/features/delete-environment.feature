Feature: Delete environment

  Scenario: delete an environment that exists
    Given multiple stacks exist
    When we run delete env
    Then the env is deleted

  Scenario: delete an environment that does not exist
    Given multiple stacks exist
    When we run delete env
    Then the env is deleted

  Scenario: delete an environment that partially exists
    Given multiple stacks exist
    When we run delete env
    Then the env is deleted

  Scenario: delete an environment without template
    Given multiple stacks exist
    When we run delete env
    Then the env is deleted
