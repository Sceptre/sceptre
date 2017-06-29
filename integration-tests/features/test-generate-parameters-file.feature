Feature: test sceptre's generate-parameter-file

  Scenario: check sceptre can create a json parameters file
    Given the generate-parameter-file command is run
    Then the parameters file json syntax is correct
    And the parameters file contains a valid cidr range