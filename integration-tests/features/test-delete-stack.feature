Feature: test sceptre's delete-stack

  Scenario: check sceptre deletes a stack
    Given a stack exists
    When we run delete stack
    Then the stack is deleted
