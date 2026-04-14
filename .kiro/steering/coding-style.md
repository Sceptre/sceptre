---
inclusion: always
---

# Coding Style

## Immutability

Prefer immutable patterns where practical:
- Return new objects/dicts rather than mutating in place
- Use `tuple` over `list` for fixed collections
- Use `frozenset` for immutable sets
- Use `dataclasses(frozen=True)` or Pydantic `model_config = ConfigDict(frozen=True)` for value objects

## File Organization

MANY SMALL FILES > FEW LARGE FILES:
- High cohesion, low coupling
- 200-400 lines typical, 500 max
- Extract utilities from large modules
- Organize by feature/domain, not by type

## Error Handling

ALWAYS handle errors comprehensively:
- Handle errors explicitly at every level
- Use specific exception types, never bare `except:`
- Log detailed error context with `logging` module
- Never silently swallow errors
- Use try/except with specific exceptions

## Input Validation

ALWAYS validate at system boundaries:
- Validate all user input before processing
- Use Pydantic models or schema-based validation
- Fail fast with clear error messages
- Never trust external data (API responses, user input, file content)

## Naming Conventions

- Functions/variables: `snake_case` (`get_user_by_id`, `calculate_total`)
- Classes: `PascalCase` (`UserService`, `DocumentProcessor`)
- Booleans: `is_`/`has_`/`should_` prefix (`is_active`, `has_permission`)
- Constants: `UPPER_SNAKE_CASE` for true constants
- Files/modules: `snake_case` matching class or purpose
- Private: prefix with `_` (`_internal_helper`)

## Code Quality Checklist

Before marking work complete:
- [ ] Code is readable and well-named
- [ ] Functions are small (<50 lines)
- [ ] Files are focused (<500 lines)
- [ ] No deep nesting (>4 levels — use early returns)
- [ ] Proper error handling at every level
- [ ] No hardcoded values (use constants or config)
- [ ] Type hints on all function signatures
- [ ] No `print()` left in production code (use `logging`)
- [ ] Docstrings on public functions and classes
