@s3-template-handler
Feature: Generate template s3

  Scenario: Generating static templates with S3 template handler
    Given the template for stack "13/B" is "valid_template.json"
    When the user generates the template for stack "13/B"
    Then the output is the same as the contents of "valid_template.json" template

  Scenario: Render jinja templates with S3 template handler
    Given the template for stack "13/C" is "jinja/valid_template.j2"
    When the user generates the template for stack "13/C"
    Then the output is the same as the contents of "valid_template.json" template

  Scenario: Render python templates with S3 template handler
    Given the template for stack "13/D" is "python/valid_template.py"
    When the user generates the template for stack "13/D"
    Then the output is the same as the contents of "valid_template.json" template
