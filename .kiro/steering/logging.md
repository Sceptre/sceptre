---
inclusion: always
description: Logging conventions and standards
---

# Logging

## Levels
- `DEBUG` — detailed diagnostic info, development only
- `INFO` — routine operations, request handling, state changes
- `WARNING` — unexpected but recoverable situations
- `ERROR` — failures that need attention but don't crash the app
- `CRITICAL` — system-level failures requiring immediate action

## Conventions
- Use the `logging` module, never `print()` in production code
- Include context: who, what, why (user ID, operation, relevant IDs)
- Use structured logging (key-value pairs) for machine-parseable output
- Set appropriate log levels per environment (DEBUG in dev, INFO in prod)

## Security
- Never log secrets, passwords, tokens, or API keys
- Sanitize PII before logging (mask emails, redact names)
- Don't log full request/response bodies in production
- Audit log output regularly for sensitive data leaks
