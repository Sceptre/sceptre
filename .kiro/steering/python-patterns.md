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

# BAD: Bare except
try:
    result = process_data(input_data)
except:  # Catches everything including KeyboardInterrupt
    pass  # Silently swallows errors
```

## Project Structure

- Use `__init__.py` to define public API of packages
- Separate concerns: models, services, routes, utils
- Use dataclasses or Pydantic models for structured data
- Keep modules focused and under 500 lines

## Async

- Use `async/await` for I/O-bound operations
- Use `asyncio.gather()` for concurrent tasks
- Don't mix sync and async code without proper bridging
- Use `aiohttp` or `httpx` for async HTTP calls

## Testing

- Use pytest over unittest
- Use fixtures for test setup/teardown
- Use parametrize for testing multiple inputs
- Mock external dependencies with `unittest.mock` or `pytest-mock`
