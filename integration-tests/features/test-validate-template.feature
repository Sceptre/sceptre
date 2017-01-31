Feature: test sceptre's validate-template

  Scenario: check sceptre can validate a template
    When validate template is run
    Then the template is marked as valid
