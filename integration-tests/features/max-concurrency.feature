Feature: Max Concurrency

  Scenario: launch stack group with max-concurrency of 1 uses single thread
    Given stack "1/A" does not exist
    And stack "1/B" does not exist
    And the template for stack "1/A" is "valid_template.json"
    And the template for stack "1/B" is "valid_template.json"
    When the user launches stack_group "1" with max-concurrency 1
    Then the executor used 1 thread
    And stack "1/A" exists in "CREATE_COMPLETE" state
    And stack "1/B" exists in "CREATE_COMPLETE" state

  Scenario: launch stack group with max-concurrency of 2 uses two threads
    Given stack "1/A" does not exist
    And stack "1/B" does not exist
    And the template for stack "1/A" is "valid_template.json"
    And the template for stack "1/B" is "valid_template.json"
    When the user launches stack_group "1" with max-concurrency 2
    Then the executor used 2 threads
    And stack "1/A" exists in "CREATE_COMPLETE" state
    And stack "1/B" exists in "CREATE_COMPLETE" state

  Scenario: launch stack group without max-concurrency uses natural concurrency
    Given stack "1/A" does not exist
    And stack "1/B" does not exist
    And the template for stack "1/A" is "valid_template.json"
    And the template for stack "1/B" is "valid_template.json"
    When the user launches stack_group "1"
    Then the executor used at least 1 thread
    And stack "1/A" exists in "CREATE_COMPLETE" state
    And stack "1/B" exists in "CREATE_COMPLETE" state
