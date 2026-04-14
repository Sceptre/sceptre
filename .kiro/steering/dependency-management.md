---
inclusion: always
description: Dependency management rules and practices
---

# Dependency Management

## Adding Dependencies
- Justify each new dependency with clear technical value
- Prefer well-maintained libraries with active communities
- Check license compatibility before adding
- Pin versions in lock files for reproducible builds

## Maintenance
- Update dependencies regularly, review changelogs
- Run security audits (`pip-audit`, `safety check`)
- Remove unused dependencies promptly
- Test after every dependency update

## Version Constraints
- Use compatible release operators (`^`, `~`) for libraries
- Pin exact versions only when necessary for stability
- Document why specific version constraints exist
- Keep lock files committed to version control
