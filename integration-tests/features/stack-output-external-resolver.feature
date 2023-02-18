Feature: Stack output external resolver

  Scenario: launch a stack referencing the external output of an existing stack with region and profile
    Given stack "external-stack-output/outputter" exists using "dependencies/independent_template.json"
    And stack "external/resolver-with-profile-region" does not exist
    When the user launches stack "external/resolver-with-profile-region"
    Then stack "external/resolver-with-profile-region" exists in "CREATE_COMPLETE" state

  Scenario: launch a stack referencing the external output of an existing stack without explicit region or profile
    Given stack "external-stack-output/outputter" exists using "dependencies/independent_template.json"
    And stack "external/resolver-no-profile-region" does not exist
    When the user launches stack "external/resolver-no-profile-region"
    Then stack "external/resolver-no-profile-region" exists in "CREATE_COMPLETE" state
