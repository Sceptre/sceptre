Feature: Project Dependencies managed within Sceptre

  Scenario: launch stack group with project dependencies within the stack
    Given stack_group "project-deps" does not exist
    And all files in template bucket for stack "project-deps/resource" are deleted at cleanup
    When the user launches stack_group "project-deps"
    Then all the stacks in stack_group "project-deps" are in "CREATE_COMPLETE"

  Scenario: template_bucket_name is managed in project
    Given stack_group "project-deps" does not exist
    And all files in template bucket for stack "project-deps/resource" are deleted at cleanup
    When the user launches stack_group "project-deps"
    Then the template for stack "project-deps/resource" has been uploaded

  Scenario: role_arn is managed in project
    Given stack_group "project-deps" does not exist
    And all files in template bucket for stack "project-deps/resource" are deleted at cleanup
    When the user launches stack_group "project-deps"
    Then the stack "project-deps/resource" has a role defined by stack "project-deps/role"

  Scenario: notifications are managed in project
    Given stack_group "project-deps" does not exist
    And all files in template bucket for stack "project-deps/resource" are deleted at cleanup
    When the user launches stack_group "project-deps"
    Then the stack "project-deps/resource" has a notification defined by stack "project-deps/topic"
