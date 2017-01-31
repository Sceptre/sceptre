Feature: test sceptre's describe-env and describe-env-resources

  Scenario: check sceptre describes an env
    Given multiple stacks exist
    Then the env is described

  Scenario: check sceptre describes an env resources
    # Stacks remain from previous Scenario
    Then the env resources are described
