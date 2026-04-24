---
inclusion: always
description: Dependency management rules and practices
---

# Dependency Management

## Package Manager

This project uses **Poetry** as the package manager. Always use `poetry` commands instead of `pip`, `uv`, or other tools.

- Add a dependency: `poetry add <package>`
- Add a dev dependency: `poetry add --group dev <package>`
- Remove a dependency: `poetry remove <package>`
- Install from lock file: `poetry install`
- Run a command in the project venv: `poetry run <command>`
- Update lock file: `poetry lock`

## Adding Dependencies
- Justify each new dependency with clear technical value
- Prefer well-maintained libraries with active communities
- Check license compatibility before adding
- Lock file (`poetry.lock`) ensures reproducible builds

## Maintenance
- Update dependencies regularly, review changelogs
- Run security audits (`poetry run pip-audit`)
- Remove unused dependencies promptly (`poetry remove <package>`)
- Test after every dependency update (`poetry run pytest`)

## Version Constraints
- Use compatible release operators (`^`, `~`) for libraries in `pyproject.toml`
- Pin exact versions only when necessary for stability
- Document why specific version constraints exist
- Always commit `poetry.lock` to version control
