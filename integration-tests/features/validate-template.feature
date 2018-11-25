Feature: Validate template

  Scenario: validate a vaild template
    Given the template for stack "1/A" is "valid_template.json"
    When the user validates the template for stack "1/A"
    Then the user is told "the template is valid"

  Scenario: validate a invaild template
    Given the template for stack "1/A" is "malformed_template.json"
    When the user validates the template for stack "1/A"
    Then a "ClientError" is raised
    and the user is told "the template is malformed"

  Scenario: validate a vaild template with ignore dependencies
    Given the template for stack "1/A" is "valid_template.json"
    When the user validates the template for stack "1/A" with ignore dependencies
    Then the user is told "the template is valid"

