---
inclusion: manual
---

# Code Review Skill

Activate this skill to perform a structured code review on recent changes.

## Review Process

1. **Gather context** — Look at the diff or changed files
2. **Understand scope** — What feature/fix do these changes relate to?
3. **Read surrounding code** — Don't review in isolation
4. **Apply checklist** — Work through categories from CRITICAL to LOW
5. **Report findings** — Only report issues you're >80% confident about

## Review Checklist

### CRITICAL — Security
- Hardcoded secrets (API keys, passwords, tokens)
- SQL injection (string concatenation in queries — use parameterized queries)
- `eval()` / `exec()` with external input
- `pickle.loads()` on untrusted data
- Missing auth checks on protected endpoints
- Exposed secrets in logs

### HIGH — Code Quality
- Large functions (>50 lines) — split them
- Large files (>500 lines) — extract modules
- Deep nesting (>4 levels) — use early returns
- Missing error handling — bare `except:`, empty except blocks
- Missing type hints on public functions
- Dead code — unused imports, commented-out code
- Missing tests for new code paths

### MEDIUM — Maintainability
- Unclear naming — variables/functions should describe their purpose
- Missing docstrings on public functions and classes
- Duplicated code that should be extracted
- Inconsistent patterns within the codebase
- Magic numbers without named constants
- `print()` statements left in production code (use `logging`)

### LOW — Style
- PEP 8 formatting inconsistencies (should be caught by black/flake8)
- Import ordering (should be caught by isort)
- Trailing whitespace

## Output Format

For each finding:
```
[SEVERITY] file:line — Description
  → Suggestion: How to fix it
```

## Rules

- Only flag issues you're confident about (>80%)
- Don't flood with noise — consolidate similar issues
- Prioritize issues that could cause bugs, security holes, or data loss
- Skip stylistic preferences unless they violate project conventions
- Be constructive — suggest fixes, not just problems
