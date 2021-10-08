Feature: Stack Diff
  Scenario Outline: Diff on stack that exists with no changes
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    And the template for stack "1/A" is "valid_template.json"
    When the user diffs stack "1/A" with "<diff_type>"
    Then a diff is returned with no "template" difference
    And a diff is returned with no "config" difference
    And a diff is returned with "is_deployed" = "True"

    Examples: DiffTypes
      | diff_type |
      | deepdiff  |
      | difflib   |

  Scenario Outline: Diff on stack that doesnt exist
    Given stack "1/A" does not exist
    And the template for stack "1/A" is "valid_template.json"
    When the user diffs stack "1/A" with "<diff_type>"
    Then a diff is returned with "is_deployed" = "False"
    And a diff is returned with a "template" difference
    And a diff is returned with a "config" difference

    Examples: DiffTypes
      | diff_type |
      | deepdiff  |
      | difflib   |

  Scenario Outline: Diff on stack that exists in non-deployed state
    Given stack "1/A" exists in "<status>" state
    And the template for stack "1/A" is "valid_template.json"
    When the user diffs stack "1/A" with "<diff_type>"
    Then a diff is returned with a "template" difference
    And a diff is returned with a "config" difference
    And a diff is returned with "is_deployed" = "False"

    Examples: DeepDiff
      | diff_type | status            |
      | deepdiff  | CREATE_FAILED     |
      | deepdiff  | ROLLBACK_COMPLETE |
      | difflib   | CREATE_FAILED     |
      | difflib   | ROLLBACK_COMPLETE |

  Scenario Outline: Diff on stack with only template changes
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    And the template for stack "1/A" is "updated_template.json"
    When the user diffs stack "1/A" with "<diff_type>"
    Then a diff is returned with a "template" difference
    And a diff is returned with no "config" difference

    Examples: DiffTypes
      | diff_type |
      | deepdiff  |
      | difflib   |

  Scenario Outline: Diff on stack with only configuration changes
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    And the template for stack "1/A" is "valid_template.json"
    And the stack config for stack "1/A" has changed
    When the user diffs stack "1/A" with "<diff_type>"
    Then a diff is returned with a "config" difference
    And a diff is returned with no "template" difference

    Examples: DiffTypes
      | diff_type |
      | deepdiff  |
      | difflib   |


  Scenario Outline: Diff on stack with both configuration and template changes
    Given stack "1/A" exists in "CREATE_COMPLETE" state
    And the template for stack "1/A" is "updated_template.json"
    And the stack config for stack "1/A" has changed
    When the user diffs stack "1/A" with "<diff_type>"
    Then a diff is returned with a "config" difference
    And a diff is returned with a "template" difference

    Examples: DiffTypes
      | diff_type |
      | deepdiff  |
      | difflib   |
