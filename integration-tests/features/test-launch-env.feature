Feature: test sceptre's launch-env

  Scenario: check sceptre launches an environment
    When we run launch env
    Then an env is created
