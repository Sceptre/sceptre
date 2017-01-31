Feature: test sceptre's update-stack

  Scenario: check sceptre updates a stack
    Given a vpc stack exists
    When the stack config is changed
    And we run update stack
    Then the stack is updated
