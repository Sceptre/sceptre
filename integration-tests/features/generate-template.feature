Feature: Generate template

  Scenario: generate template using a invaild json template
    Given the "json" template for stack "A" is valid
    When the user generates the template for stack "A"
    Then the correct template is outputted

  Scenario: generate template using a invaild json template
    Given the "yaml" template for stack "A" is valid
    When the user generates the template for stack "A"
    Then the user is told the template is invalid

  Scenario: generate template using a invaild json template
    Given the "json" template for stack "A" is invalid
    When the user validates the template for stack "A"
    Then the user is told the template is invalid

  Scenario: generate template using a invaild json template
    Given the "yaml" template for stack "A" is invalid
    When the user validates the template for stack "A"
    Then the user is told the template is invalid

#   Examples:
#   | type  | error   |
#   | json  | valid   |
#   | json  | invalid |
#   | yaml  | valid   |
#   | yaml  | invalid |
# json valid/invalid
# yaml valid/invalid
# python
#   missing handler
#   handler incorrect argument
#   another attribute error
#   another parsing error
#   python path set
#   not a string returned
