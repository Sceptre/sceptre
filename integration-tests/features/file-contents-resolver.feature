Feature: File contents resolver

  Scenario: launch a stack using the file contents resolver
    Given stack "6/2/B" does not exist
    and the file "data/example.txt" exists with "some_value"
    When the user launches stack "6/2/B"
    Then stack "6/2/B" exists in "CREATE_COMPLETE" state

  Scenario: launch a stack using the file contents resolver
    Given stack "6/2/B" does not exist
    and the file "data/example.txt" does not exist
    When the user launches stack "6/2/B"
    Then a "IOError" is raised
