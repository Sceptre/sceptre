---
inclusion: manual
---

# E2E Testing Skill

Activate this skill when writing end-to-end or integration tests for sceptre-mcp-server.

## Test Structure

### Fixture Pattern
Encapsulate setup in reusable pytest fixtures:

```python
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def sceptre_project(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return str(tmp_path)

@pytest.fixture
def mock_plan():
    with patch("sceptre_mcp_server.server.SceptrePlan") as mock:
        plan = MagicMock()
        mock.return_value = plan
        yield plan
```

## Best Practices

- Use pytest fixtures for test setup/teardown
- Use `pytest.mark.parametrize` for multiple input scenarios
- Test user-observable behavior, not internal implementation
- Keep tests independent — each test starts from a clean state
- Mock Sceptre internals (`SceptrePlan`, `SceptreContext`) for unit tests
- Use `tmp_path` fixture for temporary project directories

## What to Test E2E

- Full tool flow: MCP tool call → Sceptre command → formatted response
- Error scenarios: invalid project dir, missing config/, path traversal
- All 22 MCP tools return expected response format
- Diff tool with both deepdiff and difflib modes
- Change set lifecycle: create → describe → list → execute → delete

## What NOT to Test E2E

- Sceptre internals (tested by the sceptre project itself)
- AWS API behavior (mock at the Sceptre plan level)
- Every possible CloudFormation error (use parametrize in unit tests)

## Debugging Failed Tests

1. Check pytest output with `-v` and `--tb=long`
2. Look at mock call args to verify correct API calls
3. Run the specific test in isolation: `poetry run pytest -k "test_name" -s`
4. Add `breakpoint()` to stop at a specific point
5. Check fixture teardown for leftover state
