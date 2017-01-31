Feature: test sceptre's generate-template

  Scenario: check sceptre can create a json template
    Given the generate-template command is run
    Then the template json syntax is correct
    And the template contains a vpc
