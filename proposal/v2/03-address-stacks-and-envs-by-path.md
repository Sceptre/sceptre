# 03 Address stacks and envs by path

## Implementation

We currently build stacks and environments with the syntax:

```
sceptre <action>-stack env stack
sceptre <action>-env env
```

This proposal would change the addressing to:

```
sceptre <action> path/to/stack.yaml
sceptre <action> --recursive path/to/env/
```

## Pros
- By supplying file paths, we get native tab completion (only tested on `zsh` on `macOS`)

## Cons
