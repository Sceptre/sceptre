---
inclusion: manual
---

# E2E Testing Skill

Activate this skill when writing end-to-end or integration tests for Sceptre.

## Framework

This project uses the [behave](https://behave.readthedocs.io/) BDD framework
for end-to-end testing. Tests are written in Gherkin syntax (`.feature` files)
with Python step implementations.

## Project Structure

```
integration-tests/
├── features/           # Gherkin .feature files
│   ├── create-stack.feature
│   ├── launch-stack.feature
│   └── ...
├── steps/              # Python step implementations
│   ├── stacks.py
│   ├── stack_groups.py
│   ├── change_sets.py
│   ├── helpers.py
│   └── ...
├── sceptre-project/    # Fixture Sceptre project
│   ├── config/
│   └── templates/
├── environment.py      # behave hooks (before_all, before_scenario, etc.)
└── __ini__.py
```

## Writing Feature Files

Use Gherkin syntax with existing step definitions where possible:

```gherkin
Feature: Launch stack

  Scenario: launch a new stack
    Given stack "1/A" does not exist
    And the template for stack "1/A" is "valid_template.json"
    When the user launches stack "1/A"
    Then stack "1/A" exists in "CREATE_COMPLETE" state
```

## Writing Step Definitions

Step definitions live in `integration-tests/steps/`. Use the `@given`, `@when`,
`@then` decorators from behave:

```python
from behave import given, when, then

@when('the user launches stack "{stack_name}"')
def step_impl(context, stack_name):
    launch_stack(context, stack_name)
```

Key conventions:
- Reuse existing steps from `stacks.py`, `stack_groups.py`, `change_sets.py`
- Helper functions go in `helpers.py`
- Use `context` to share state between steps
- Use `context.error` to capture exceptions for error scenarios

## Running Tests

```bash
# Run all integration tests
poetry run behave integration-tests/features

# Run a specific feature
poetry run behave integration-tests/features/launch-stack.feature

# Run with JUnit output
poetry run behave integration-tests/features --junit --junit-directory build/behave
```

## Environment Setup

The `environment.py` file handles:
- `before_all`: Creates unique project code, sets up AWS clients, updates config
- `before_scenario`: Resets error/response/output state
- `after_all`: Cleans up all stacks created during the test run

Tests require AWS credentials and run against a real AWS account.

## Best Practices

- Each scenario should be independent — don't rely on state from other scenarios
- Use `Given` steps to set up preconditions (create/delete stacks as needed)
- Use `retry_boto_call` from `helpers.py` for AWS API calls (handles throttling)
- Keep feature files focused on one capability per file
- Use descriptive scenario names that explain the behavior being tested
- Wait for stacks to reach final state before asserting

## What to Test E2E

- Stack lifecycle: create, update, delete, launch
- Stack group operations: launch group, delete group
- Change set lifecycle: create, describe, execute, delete
- Dependency resolution between stacks
- Template validation and drift detection
- Stack diff with deepdiff and difflib modes
- Prune operations for obsolete stacks

## What NOT to Test E2E

- Sceptre internal logic (covered by unit tests in `tests/`)
- Every possible CloudFormation error
- CLI argument parsing (covered by unit tests in `tests/test_cli/`)

## Debugging Failed Tests

1. Run the specific feature with verbose output: `poetry run behave -v integration-tests/features/launch-stack.feature`
2. Check `context.error` in step definitions for captured exceptions
3. Look at CloudFormation console for stack events
4. Use `wait_for_final_state` to ensure stacks reach a terminal state before assertions
5. Check `environment.py` `after_all` for cleanup issues
