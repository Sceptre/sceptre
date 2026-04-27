---
inclusion: always
description: Documentation standards and conventions
---

# Documentation

## Code Documentation
- Docstrings on all public functions, classes, and modules
- Explain "why" in comments, not "what" (code shows what)
- Type hints on all function signatures
- Document non-obvious side effects and assumptions

## Project Documentation
- Documentation is written in reStructuredText (`.rst`) and built with Sphinx
- Source files live in `docs/_source/docs/`
- Build locally with `poetry run make html --directory docs`
- Published via [readthedocs.org](https://sceptre.readthedocs.io) on every change

## Writing reStructuredText
- Use `.rst` files, not Markdown, for project documentation
- Section headings use underlines: `=` for titles, `-` for sections, `~` for subsections
- Use `.. code-block:: yaml` (or `python`, `jinja`, `text`) for code examples
- Use `.. note::` and `.. warning::` directives for callouts
- Cross-reference other docs with backtick links: `` `Templates <templates.html#jinja>`_ ``

## Maintenance
- Update docs when changing behavior
- Remove outdated documentation promptly
- Review docs as part of code review
