---
inclusion: always
description: Error handling patterns and conventions
---

# Error Handling

## Principles
- Handle errors explicitly at every level
- Use specific exception types, never bare `except:`
- Fail fast with clear, actionable error messages
- Never silently swallow errors
- Log error context before re-raising

## Patterns
- Use custom exception classes for domain errors
- Return structured error responses from APIs (`{ error, message, details }`)
- Use early returns to handle error cases first, keep happy path unindented
- Wrap external calls (APIs, DB, file I/O) in try/except with specific exceptions
- Include correlation IDs in error responses for traceability

## Anti-Patterns
- Bare `except:` or `except Exception:` without re-raising
- Catching and ignoring errors silently
- Returning `None` to signal errors instead of raising
- Leaking stack traces or internal details in user-facing errors
- Using exceptions for control flow
