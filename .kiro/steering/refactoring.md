---
inclusion: manual
---

# Refactoring Skill

Activate this skill for safe, systematic code improvement.

## Refactoring Principles

- **Tests first** — Ensure test coverage exists before refactoring
- **Small steps** — One change at a time, verify tests pass after each
- **No behavior change** — Refactoring changes structure, not behavior
- **Commit often** — Each successful refactoring step gets its own commit

## Common Refactoring Patterns

### Extract Function
When a block of code does something that can be named:
```python
# Before: inline logic
if user.age >= 18 and user.verified and not user.banned:
    ...

# After: extracted with clear name
if is_eligible_user(user):
    ...
```

### Early Return
When deep nesting makes code hard to follow:
```python
# Before: nested
def process(data):
    if data:
        if data.get("valid"):
            # actual logic

# After: early returns
def process(data):
    if not data:
        return
    if not data.get("valid"):
        return
    # actual logic
```

### Replace Magic Numbers
```python
# Before
if retries > 3:
    ...

# After
MAX_RETRIES = 3
if retries > MAX_RETRIES:
    ...
```

### Split Large Files
When a file exceeds 500 lines:
1. Identify distinct responsibilities
2. Extract each into its own module
3. Re-export from original `__init__.py` if needed for backward compatibility
4. Update imports across codebase

### Dead Code Removal
- Remove commented-out code (it's in git history)
- Remove unused imports (use `autoflake` or `ruff`)
- Remove unreachable branches
- Remove unused functions/variables

## Workflow

1. Identify the smell (large file, deep nesting, duplication, etc.)
2. Verify test coverage exists for affected code
3. Apply one refactoring pattern
4. Run tests — must still pass (`pytest -q`)
5. Commit
6. Repeat

## Red Flags That Need Refactoring

- Functions over 50 lines
- Files over 500 lines
- Nesting deeper than 4 levels
- Duplicated code in 3+ places
- God classes/functions that do everything
- Long parameter lists (>4 params — use a dataclass or TypedDict)
