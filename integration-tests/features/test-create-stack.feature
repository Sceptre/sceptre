Feature: test sceptre's create-stack

  Scenario: check sceptre creates a stack
    When we run create stack
    Then a stack is created
    And all its resources are created
