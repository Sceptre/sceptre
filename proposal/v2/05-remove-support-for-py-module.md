# 05 Remove official support for Sceptre use as a Python module

Sceptre officially supports use via the CLI and as a Python module. Use via the CLI is far more common (I'm not sure if anyone uses Sceptre as a Python module). We guarantee that both our CLI and public Python APIs won't change. Guaranteeing the Python API leads to two problems:

- It makes it difficult to refactor the inner workings of Sceptre
- It makes our versioning unusual, as we are effectively versioning two independent APIs with a single version number. If we commit a breaking change to Sceptre's Python internals, we must bump our major version number, even though users of Sceptre as a CLI tool (most of our users) would see no change.

This would be a relatively superficial change. Our Python function and classes would still be public, and people could still use Sceptre as a module, but we wouldn't officially support it or guarantee its API.

## Implementation

Remove references to use as a Python module from the documentation.

## Pros
- Reduces our public API
- Makes it easier to develop Sceptre as we have fewer contracts to uphold
- Makes our versioning less strange

## Cons
- Discontinued support for Python module
