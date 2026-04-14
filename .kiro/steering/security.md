---
inclusion: always
---

# Security Guidelines

## Mandatory Checks Before Any Commit

- [ ] No hardcoded secrets (API keys, passwords, tokens, connection strings)
- [ ] All user inputs validated and sanitized
- [ ] SQL injection prevention (parameterized queries only)
- [ ] Authentication/authorization verified on protected endpoints
- [ ] Error messages don't leak sensitive data or stack traces
- [ ] No sensitive data in logs

## Secret Management

- NEVER hardcode secrets in source code
- ALWAYS use environment variables or AWS Secrets Manager
- Validate required secrets are present at startup
- Rotate any secrets that may have been exposed
- Use .env files locally, never commit them

## OWASP Top 10 Awareness

When writing code that handles user input, auth, or data:
1. **Injection** — Always use parameterized queries (SQLAlchemy bind params, psycopg2 `%s` placeholders)
2. **Broken Auth** — Hash passwords (bcrypt/argon2), validate tokens properly
3. **Sensitive Data** — Encrypt PII, enforce HTTPS, sanitize logs
4. **Broken Access Control** — Check auth on every endpoint
5. **Misconfiguration** — No default creds, debug mode off in prod
6. **Known Vulnerabilities** — Keep dependencies updated, run `pip-audit` or `safety check`

## Dangerous Patterns to Flag Immediately

| Pattern | Severity | Fix |
|---------|----------|-----|
| Hardcoded secrets | CRITICAL | Use `os.environ` or Secrets Manager |
| String-concatenated SQL | CRITICAL | Parameterized queries |
| `eval()` / `exec()` with user input | CRITICAL | Never use with external data |
| `pickle.loads()` on untrusted data | CRITICAL | Use JSON or safe deserialization |
| No auth check on endpoint | CRITICAL | Add auth decorator/middleware |
| Logging passwords/tokens | MEDIUM | Sanitize log output |
| `subprocess.shell=True` with user input | HIGH | Use `subprocess.run()` with list args |

## If a Security Issue Is Found

1. STOP current work
2. Fix the vulnerability immediately
3. Rotate any exposed secrets
4. Check for similar issues elsewhere in codebase
