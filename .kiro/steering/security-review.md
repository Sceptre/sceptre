---
inclusion: manual
---

# Security Review Skill

Activate this skill to perform a security audit on the codebase or recent changes.

## Audit Process

### 1. Secrets Scan
- Search for hardcoded API keys, passwords, tokens, connection strings
- Check .env files are in .gitignore
- Verify secrets are loaded from `os.environ` or AWS Secrets Manager
- Look for secrets in comments, TODOs, or test files

### 2. OWASP Top 10 Check

| # | Vulnerability | What to Check |
|---|--------------|---------------|
| 1 | Injection | All queries parameterized? (SQLAlchemy, psycopg2 `%s`) User input sanitized? |
| 2 | Broken Auth | Tokens validated? Sessions secure? |
| 3 | Sensitive Data | HTTPS enforced? PII encrypted? Logs sanitized? |
| 4 | Broken Access | Auth checked on every endpoint? IAM least-privilege? |
| 5 | Misconfiguration | Default creds changed? Debug off in prod? Security headers? |
| 6 | Known Vulnerabilities | Dependencies up to date? `pip-audit` clean? |
| 7 | Insecure Deserialization | `pickle.loads()` on untrusted data? |
| 8 | Insufficient Logging | Security events logged? Alerts configured? |

### 3. Dependency Audit
- Run `pip-audit` or `safety check`
- Check for known CVEs in dependencies
- Verify `requirements.txt` / `poetry.lock` are committed
- Remove unused dependencies

### 4. Dangerous Code Patterns

Flag these immediately:
- `eval()` / `exec()` with any external input
- `subprocess` with `shell=True` and user-provided strings
- `pickle.loads()` on untrusted data
- `os.system()` with user-controlled strings
- Plaintext secret comparison
- Database queries with string concatenation instead of parameterization
- File operations with user-controlled paths (path traversal risk)

## Output Format

```
[CRITICAL/HIGH/MEDIUM/LOW] Category — Description
  Location: file:line
  Risk: What could go wrong
  Fix: How to remediate
```

## Emergency Protocol

If CRITICAL vulnerability found:
1. Document it immediately
2. Fix before any other work
3. Rotate exposed secrets
4. Check for similar issues elsewhere
