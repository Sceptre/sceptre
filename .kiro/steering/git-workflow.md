---
inclusion: always
---

# Git Workflow

## Commit Messages

Use conventional commit format: `type(scope): description`

Types: feat, fix, docs, style, refactor, test, chore
- Keep first line under 50 characters
- Use imperative mood ("Add feature" not "Added feature")
- Include body for complex changes

Examples:
```
feat(connector): add Confluence incremental sync
fix(rag): handle Bedrock timeout with retry
refactor(identity): extract group mapping logic
test(slack-ingress): add signature validation tests
```

## Branching

- Feature branches for new development: `feature/confluence-connector`
- Bug fix branches: `fix/opensearch-timeout`
- Keep `main` stable and deployable
- Delete merged branches

## Before Committing

- [ ] Run tests and verify they pass (`pytest -q`)
- [ ] No hardcoded secrets or API keys
- [ ] No `print()` or debug logging left in code
- [ ] Changes are logically grouped (atomic commits)
- [ ] Commit message follows conventional format

## Security

- NEVER commit secrets, API keys, or passwords
- Use environment variables or AWS Secrets Manager
- Review diffs for sensitive information before pushing
- Use .gitignore to exclude `cdk.out/`, `.venv/`, `__pycache__/`, `.env` files
