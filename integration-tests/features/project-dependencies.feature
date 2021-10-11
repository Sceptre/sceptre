Feature: Project Dependencies managed within Sceptre

  Scenario: launch stack group with project dependencies within the stack
    Given stack_group "managed-project-dependencies" does not exist
    And all files in template bucket for stack "managed-project-dependencies/resource" are deleted at cleanup
    When the user launches stack_group "managed-project-dependencies"
    Then all the stacks in stack_group "managed-project-dependencies" are in "CREATE_COMPLETE"

  Scenario: template bucket is managed in project
    Given stack_group "managed-project-dependencies" does not exist
    And all files in template bucket for stack "managed-project-dependencies/resource" are deleted at cleanup
    When the user launches stack_group "managed-project-dependencies"
    Then the template for stack "managed-project-dependencies/resource" has been uploaded
