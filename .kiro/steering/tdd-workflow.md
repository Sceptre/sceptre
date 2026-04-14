---
inclusion: manual
---

# TDD Workflow Skill

Activate this skill when implementing new features, fixing bugs, or refactoring Python code.

## The Cycle: RED → GREEN → REFACTOR

### Step 1: Define the Interface (SCAFFOLD)
- Define type hints and function signatures
- Create function/class stubs that raise `NotImplementedError`
- Clarify the contract before writing any logic

### Step 2: Write Failing Tests (RED)
- Write tests that describe the desired behavior
- Cover happy path, edge cases, and error scenarios
- Run tests — they MUST fail (`pytest -q`)

### Step 3: Implement Minimal Code (GREEN)
- Write the simplest code that makes all tests pass
- Don't optimize yet — just make it work
- Run tests — they should all pass now

### Step 4: Refactor (IMPROVE)
- Clean up the implementation while keeping tests green
- Extract constants, improve naming, reduce duplication
- Run tests after each refactoring step

### Step 5: Verify Coverage
- Check coverage is at 80%+: `pytest --cov --cov-report=term-missing -q`
- Add tests for any uncovered paths
- Focus on meaningful coverage, not just line count

## Test Structure Template

```python
import pytest
from unittest.mock import MagicMock, patch


class TestModuleName:
    """Tests for [Module/Function Name]."""

    def test_happy_path_when_valid_input(self):
        # Arrange
        input_data = {...}
        # Act
        result = function_under_test(input_data)
        # Assert
        assert result == expected

    def test_raises_value_error_on_empty_input(self):
        with pytest.raises(ValueError, match="Input cannot be empty"):
            function_under_test({})

    @pytest.mark.parametrize("input,expected", [
        (None, None),
        ("", ""),
        ("valid", "VALID"),
    ])
    def test_edge_cases(self, input, expected):
        assert function_under_test(input) == expected
```

## Rules

- NEVER write implementation before tests
- NEVER modify tests to make them pass (fix the implementation)
- Each test should test ONE behavior
- Tests should be independent (no shared mutable state between tests)
- Mock external dependencies (`boto3`, `opensearch`, `slack_sdk`), not internal logic
