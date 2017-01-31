Feature: test sceptre's describe-stack-resources

  Scenario: check sceptre describes stack resources
    Given a stack exists
    Then the stack resources are listed
