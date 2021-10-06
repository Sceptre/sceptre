@s3-template-handler
Feature: Generate template s3

  Scenario: Generating static template with S3 template handler
    Given the template for stack "13/B" is "valid_template.json"
    When the user generates the template for stack "13/B"
    Then the output is the same as the contents of "valid_template.json" template

  Scenario: Generating jinja template with S3 template handler
    Given the template for stack "13/D" is "jinja/valid_template.j2"
    When the user generates the template for stack "13/D"
    Then the output is the same as the contents of "jinja/valid_template.json" template

  Scenario: Generating python template with S3 template handler
    Given the template for stack "13/C" is "valid_template.py"
    When the user generates the template for stack "13/C"
    Then the output is the same as the contents of "valid_template.json" template
