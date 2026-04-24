---
inclusion: always
---

# Security Guidelines

## Mandatory Checks Before Any Commit

- [ ] No hardcoded secrets (AWS keys, passwords, tokens)
- [ ] All tool inputs validated (path traversal, null bytes, absolute paths)
- [ ] Error messages don't leak file system paths or stack traces to the agent
- [ ] No sensitive data in logs (AWS credentials, account IDs)

## Input Validation

This is an MCP server that accepts tool parameters from AI agents. Validate at the boundary:
- Reject path traversal (`..`) in `stack_path` parameters
- Reject absolute paths — only relative paths within the Sceptre project
- Reject null bytes in string parameters
- Validate `sceptre_project_dir` exists and contains `config/`

## AWS Credential Handling

- NEVER hardcode AWS credentials in source code
- Use environment variables (`AWS_PROFILE`, `AWS_DEFAULT_REGION`) or IAM roles
- Don't log AWS credentials, account IDs, or ARNs
- Credentials flow through Sceptre's standard AWS credential chain

## Dependency Security

- Keep dependencies updated regularly
- Run security audits (`poetry run pip-audit`)
- Review third-party packages before adding
- Commit `poetry.lock` for reproducible builds

## Dangerous Patterns to Flag

| Pattern | Severity | Fix |
|---------|----------|-----|
| Hardcoded AWS keys | CRITICAL | Use environment variables |
| Unvalidated `stack_path` | HIGH | Use `_validate_stack_path()` |
| `eval()` / `exec()` with tool input | CRITICAL | Never use with external data |
| Logging credentials or ARNs | MEDIUM | Sanitize log output |
| Bare `except:` swallowing errors | MEDIUM | Use specific exception types |
