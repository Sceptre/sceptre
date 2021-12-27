Feature: StackGroup Dependencies managed within Sceptre

  Background:
    Given stack_group "project-deps" does not exist

  Scenario: launch stack group with dependencies
    Given all files in template bucket for stack "project-deps/main-project/resource" are deleted at cleanup
    When the user launches stack_group "project-deps"
    Then all the stacks in stack_group "project-deps" are in "CREATE_COMPLETE"

  Scenario: template_bucket_name is managed in stack group
    Given all files in template bucket for stack "project-deps/main-project/resource" are deleted at cleanup
    When the user launches stack_group "project-deps"
    Then the template for stack "project-deps/main-project/resource" has been uploaded

  Scenario: notifications are managed in stack group
    Given all files in template bucket for stack "project-deps/main-project/resource" are deleted at cleanup
    When the user launches stack_group "project-deps"
    Then the stack "project-deps/main-project/resource" has a notification defined by stack "project-deps/dependencies/topic"
