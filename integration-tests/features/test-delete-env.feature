Feature: test sceptre's delete-env

  Scenario: check sceptre deletes an environment
    Given multiple stacks exist
    When we run delete env
    Then the env is deleted
