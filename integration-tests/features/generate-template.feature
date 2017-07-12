Feature: Generate template

  Scenario Outline: Generating static templates
    Given the template for stack "1/A" is <filename>
    When the user generates the template for stack "1/A"
    Then the output is the same as the contents of <filename> template

  Examples: Json, Yaml
    | filename                 |
    | valid_template.json      |
    | malformed_template.json  |
    | invalid_template.json    |
    | valid_template.yaml      |
    | malformed_template.yaml  |
    | invalid_template.yaml    |

  Scenario: Generate template using a valid python template file
    Given the template for stack "1/A" is valid_template.py
    When the user generates the template for stack "1/A"
    Then the output is the same as the string returned by valid_template.py

  Scenario Outline: Generating erroneous python templates
    Given the template for stack "1/A" is <filename>
    When the user generates the template for stack "1/A"
    Then the user is told the <error_message>

  Examples: Template Errors
    | filename                                | error_message                          |
    | missing_sceptre_handler.py              | template does not have sceptre_handler |
    | attribute_error.py                      | attribute error                        |

  Scenario: Generate template using a template file with an unsupported extension
    Given the template for stack "1/A" is template.unsupported
    When the user generates the template for stack "1/A"
    Then the user is told the template format is unsupported

  Scenario Outline: Rendering jinja templates
    Given the template for stack "7/A" is <filename>
    When the user generates the template for stack "7/A"
    Then the output is the same as the contents of <rendered_filename> template

  Examples: Json, Yaml, J2
    | filename                    | rendered_filename     |
    | jinja/valid_template.json   | valid_template.json   |
    | jinja/valid_template.yaml   | valid_template.yaml   |
    | jinja/valid_template.j2     | valid_template.yaml   |

  Scenario Outline: Render jinja template which uses an invalid key
    Given the template for stack "7/A" is <filename>
    When the user generates the template for stack "7/A"
    Then the user is told <error_message>

  Examples: Render Errors
    | filename                                  | error_message      |
    | jinja/invalid_template_missing_key.yaml   | key is undefined   |
    | jinja/invalid_template_missing_attr.yaml  | missing attribute  |
