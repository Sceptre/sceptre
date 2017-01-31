Feature: test sceptre's lock-stack and unlock-stack

  Scenario: check sceptre locks a stack
    Given a stack exists
    When we run lock stack
    Then the stack is locked

  Scenario: check sceptre unlocks a stack
    # Stack is still present from previous Scenario
    When we run unlock stack
    Then the stack is unlocked
