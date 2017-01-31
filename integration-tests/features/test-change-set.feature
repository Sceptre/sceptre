Feature: test sceptre's change-set

  Scenario: check sceptre creates change set
    Given a vpc stack exists
    When the stack config is changed
    And we run create change set
    Then the stack contains a change set
    # Note stack config is changed to it's original form after this Scenario

  Scenario: test describe-change-set
    Then the change set should be described

  Scenario: check sceptre list change sets
    Then the change set can be listed

  Scenario: check sceptre executes change set
    When the change set is executed
    Then the stack is updated

  Scenario: check sceptre delete change set
    Given a change set exists in the stack
    When we execute delete change set
    Then the change set should not be present in the stack
