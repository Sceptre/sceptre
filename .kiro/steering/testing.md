---
inclusion: always
---

# Testing Requirements

## Coverage Target: 80%+

All new code should have test coverage. Three test types required:

1. **Unit Tests** — Individual functions, utilities, classes (`pytest`, run with `poetry run tox`)
2. **Integration Tests** — Service interactions (`pytest` with fixtures)
3. **E2E Tests** — Critical flows using the `behave` BDD framework (see `e2e-testing.md`)

## Test-Driven Development

Preferred workflow for new features (see `tdd-workflow.md` for the full cycle):
1. Write test first (RED) — test should fail
2. Write minimal implementation (GREEN) — test should pass
3. Refactor (IMPROVE) — clean up while tests stay green
4. Verify coverage meets 80%+ (`poetry run pytest --cov`)

## Test Quality

- Test behavior, not implementation details
- Each test should have a single clear assertion focus
- Use descriptive test names that explain the scenario (`test_user_creation_fails_with_invalid_email`)
- Test edge cases: empty inputs, None values, boundary conditions, error paths
- Mock external dependencies with `unittest.mock` or `pytest-mock`, not internal logic
- Keep tests independent — no shared mutable state
- Use `pytest.fixture` for setup/teardown
- Use `pytest.mark.parametrize` for testing multiple inputs

## Troubleshooting Failures

1. Check test isolation (no shared state between tests)
2. Verify mocks are correct and up to date
3. Fix implementation, not tests (unless tests are wrong)
4. Run tests in isolation to find ordering issues (`poetry run pytest -k "test_name"`)
