# 00 Simplify create, update, delete, launch, describe CLI commands

Full change list:
```
Current:                  Proposed:
continue-update-rollback  [unchanged]
create-change-set         [unchanged]
create-stack              create
delete-change-set         [unchanged]
delete-env                delete -r
delete-stack              delete
describe-change-set       [unchanged]
describe-env              [unchanged] (maybe it would be working adding a describe-stack command for symmetry)
describe-env-resources    describe-resources -r
describe-stack-outputs    describe-outputs
describe-stack-resources  describe-resources
execute-change-set        [unchanged]
generate-template         [unchanged]
get-stack-policy          get-policy
launch-env                launch -r
launch-stack              launch
list-change-sets          [unchanged]
lock-stack                lock
set-stack-policy          set-policy
unlock-stack              unlock
update-stack              update
update-stack-cs           update-cs (maybe implement this as a flag: update -cs)
validate-template         [unchanged]
```

## Implementation

Rename CLI commands.

## Pros
- The `-r/--recursive` syntax is more in keeping with Unix standards (e.g. `cp`, `mv`, `grep`)
- Commands are less verbose

## Cons
- The original reason for having separate commands for building stacks and environments was to avoid users accidentally deleting whole environments. This would be mitigated by proposal 01.
