Feature: Stack output external resolver

  Scenario: launch a stack referencing the external output of an existing stack without explicit region or profile
    Given stack "external-stack-output/outputter" exists using "dependencies/independent_template.json"
    And stack "external-stack-output/resolver-no-profile-region" does not exist
    When the user launches stack "external-stack-output/resolver-no-profile-region"
    Then stack "external-stack-output/resolver-no-profile-region" exists in "CREATE_COMPLETE" state
