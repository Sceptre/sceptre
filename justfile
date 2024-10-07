_default:
    @just --list

# Enable direnv
enable-direnv:
    #!/usr/bin/env bash
    set -euo pipefail
    [ -f ".envrc" ] && echo ".envrc already exists" && exit
    echo "use flake" >.envrc

# Re-run recipe CMD whenever files change
watch CMD *ARGS:
    watchexec -c -r -d 500ms --print-events -- just {{CMD}} {{ARGS}}
alias w := watch

# Run tests via tox
test *ARGS:
    poetry run tox {{ARGS}}
alias t := test

# Run a single test
a-test TEST *ARGS:
    poetry run pytest -ssv {{TEST}} {{ARGS}}
alias tt := a-test
