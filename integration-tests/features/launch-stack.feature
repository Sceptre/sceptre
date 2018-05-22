Feature: Launch stack

  Scenario: launch a new stack
    Given stack "1/A" does not exist
    and the template for stack "1/A" is "valid_template.json"
    When the user launches stack "1/A"
    Then stack "1/A" exists in "CREATE_COMPLETE" state

  Scenario: launch a stack that was newly created
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and the template for stack "1/A" is "updated_template.json"
    When the user launches stack "1/A"
    Then stack "1/A" exists in "UPDATE_COMPLETE" state

  Scenario: launch a stack that has been previously updated
    Given stack "1/A" exists in "UPDATE_COMPLETE" state
    and the template for stack "1/A" is "valid_template.json"
    When the user launches stack "1/A"
    Then stack "1/A" exists in "UPDATE_COMPLETE" state

  Examples: Template
    | filename                             |
    | updated_template.json                |
    | updated_template_with_transform.yaml |

  Scenario Outline: launch an existing stack with no changes
    Given the template for stack "1/A" is "<filename>"
    and stack "1/A" exists using "<filename>"
    When the user launches stack "1/A"
    Then no exception is raised

  Examples: Template
    | filename                             |
    | updated_template.json                |
    | updated_template_with_transform.yaml |
