Feature: Import stack

  Scenario: import a config and template that do not exist in sceptre
    Given stack "3/A" exists in "CREATE_COMPLETE" state
    and stack "3/Z" does not exist in config
    and template "templates/imported.yaml" does not exist
    When the user imports AWS stack "3/A" into Sceptre stack "3/Z" and template "templates/imported.yaml"
    Then stack "3/Z" file exists in config
    and template "templates/imported.yaml" exists

  Scenario: import a config that does not exist in sceptre with a template that is the same as the named template
    Given stack "3/A" exists using "templates/valid_template.yaml"
    and stack "3/Z" does not exist in config
    and template "templates/valid_template.yaml" exists
    When the user imports AWS stack "3/A" into Sceptre stack "3/Z" and template "templates/valid_template.yaml"
    Then stack "3/Z" file exists in config
    and template "templates/valid_template.yaml" is unchanged
