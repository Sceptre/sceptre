Feature: Validate template

  @now
  Scenario: validate a vaild template
    Given the template for stack "A" is valid
    When the user validates the template for stack "A"
    Then the user is told the template is valid

  @now
  Scenario: validate a invaild template
    Given the template for stack "A" is malformed
    When the user validates the template for stack "A"
    Then the user is told the template is malformed
