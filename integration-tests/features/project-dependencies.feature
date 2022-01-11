Feature: Project Dependencies managed within Sceptre

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

  Scenario: validate a project that isn't deployed yet
    Given placeholders are allowed
    When the user validates stack_group "project-deps"
    Then the user is told "the template is valid"

  Scenario: diff a project that isn't deployed yet
    Given placeholders are allowed
    When the user diffs stack group "project-deps" with "deepdiff"
    Then a diff is returned with "is_deployed" = "False"

  Scenario: tags can be resolved
    Given all files in template bucket for stack "project-deps/main-project/resource" are deleted at cleanup
    When the user launches stack_group "project-deps"
    Then the tag "greeting" for stack "project-deps/main-project/resource" is "hello"
    And the tag "nonexistant" for stack "project-deps/main-project/resource" does not exist
