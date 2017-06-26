Feature: Generate template

  @now
  Scenario Outline: Generating static templates
    Given the template for stack "A" is <filename>
    When the user generates the template for stack A
    Then the output is the same as the contents of <filename> template

  Examples: Json and Yaml
   | filename                 |
   | valid_template.json      |
   | malformed_template.json  |
   | invalid_template.json    |
   | valid_template.yaml      |
   | malformed_template.yaml  |
   | invalid_template.yaml    |

   @wip
   Scenario: Generate template using a valid python template file
     Given the template for stack "A" is valid_template.py
     Then the output is the same as the string returned by sceptre_handler function

   @wip
   Scenario Outline: Generating erroneous python templates
     Given the template for stack "A" is <content_type>
     and the extension for template is .py
     When the user generates the template
     Then the user is told the <error_message>

   Examples: Template Errors
    | content_type                                | error_message                             |
    | missing sceptre handler                     | missing sceptre handler function          |
    # | handler accept wrong number of arguments    |
    # | another attribute error is thrown           | yaml          |
    # | not a string is return for sceptre handler  |
    # | another parsing error is thrown             |


   @wip
   Scenario: Generate template using a template file with an unsupported extension
     Given the template for stack "A" is valid
     and the extension for template is .unsupported
     When the user generates the template
     Then the user is told the template format is unsupported

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
