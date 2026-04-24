---
inclusion: fileMatch
fileMatchPattern: "**/*.py"
---

# Python Patterns

## Style

- Follow PEP 8 conventions
- Use type hints for function signatures and complex variables
- Prefer f-strings over .format() or % formatting
- Use pathlib over os.path for file operations
- Prefer list/dict/set comprehensions over manual loops when readable

## Error Handling

See `error-handling.md` for comprehensive rules. Python-specific example:

```python
# GOOD: Specific exception handling
try:
    result = process_data(input_data)
except ValueError as e:
    logger.error(f"Invalid data: {e}")
    raise
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")
    return fallback_result()
```

## Project Structure

- Use `__init__.py` to define public API of packages
- Separate concerns: models, services, routes, utils
- Use dataclasses or Pydantic models for structured data

## Testing

See `testing.md` for test requirements and `tdd-workflow.md` for the TDD cycle.

## Type Checking (mypy)

- Run with `poetry run mypy src/`
- All functions in `src/` must have type annotations (`disallow_untyped_defs = true`)
- Test files are exempt from strict typing (`tests.*` override in pyproject.toml)
- Use `Any` sparingly — prefer specific types or generics
- Use `Callable[..., str]` for callback parameters
- Use `dict[str, Any]` over bare `dict` for return types
- Use `ignore_missing_imports = true` for third-party libs without stubs (sceptre, fastmcp)
- mypy runs in pre-commit (mirrors-mypy) and CI (type-check job)
