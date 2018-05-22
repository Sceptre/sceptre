Feature: Update stack

  Scenario Outline: update a stack that was newly created
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    and the template for stack "1/A" is "<filename>"
    When the user updates stack "1/A"
    Then stack "1/A" exists in "UPDATE_COMPLETE" state

  Examples: Template
    | filename                             |
    | updated_template.json                |
    | updated_template_with_transform.yaml |

  Scenario Outline: update a stack that has been previously updated
    Given stack "1/A" exists in "UPDATE_COMPLETE" state
    and the template for stack "1/A" is "<filename>"
    When the user updates stack "1/A"
    Then stack "1/A" exists in "UPDATE_COMPLETE" state

  Examples: Template
    | filename                             |
    | updated_template.json                |
    | updated_template_with_transform.yaml |

  Scenario Outline: update a stack that does not exists
    Given stack "1/A" does not exist
    and the template for stack "1/A" is "<filename>"
    When the user updates stack "1/A"
    Then stack "1/A" does not exist

  Examples: Template
    | filename                             |
    | updated_template.json                |
    | updated_template_with_transform.yaml |
