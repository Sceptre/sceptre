@s3-template-handler
Feature: Generate template s3

  Scenario: Generating static templates with S3 template handler
    Given the template for stack "13/B" is "valid_template.json"
    When the user generates the template for stack "13/B"
    Then the output is the same as the contents of "valid_template.json" template
