Feature: Generate template

  Scenario Outline: Generating static templates
    Given the template for stack "1/A" is "<filename>"
    When the user generates the template for stack "1/A"
    Then the output is the same as the contents of "<filename>" template

  Examples: Json and Yaml
    | filename                 |
    | valid_template.json      |
    | malformed_template.json  |
    | invalid_template.json    |
    | valid_template.yaml      |
    | malformed_template.yaml  |
    | invalid_template.yaml    |

  Scenario: Generate template using a valid python template file
    Given the template for stack "1/A" is "valid_template.py"
    When the user generates the template for stack "1/A"
    Then the output is the same as the string returned by "valid_template.py"

  Scenario Outline: Generating erroneous python templates
    Given the template for stack "1/A" is "<filename>"
    When the user generates the template for stack "1/A"
    Then a "<exception>" is raised

  Examples: Template Errors
    | filename                   | exception                   |
    | missing_sceptre_handler.py | TemplateSceptreHandlerError |
    | attribute_error.py         | AttributeError              |

  Scenario: Generate template using a template file with an unsupported extension
    Given the template for stack "1/A" is "template.unsupported"
    When the user generates the template for stack "1/A"
    Then a "UnsupportedTemplateFileTypeError" is raised
