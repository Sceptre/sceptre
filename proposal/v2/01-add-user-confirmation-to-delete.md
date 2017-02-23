# 01 Add a user confirmation to delete

Sceptre should ask for user confirmation when deleting stacks or environments. A CLI flag `--yes/-y` will be added, allowing scriptable deletion of resources. This confirmation will only happen on the CLI, not when delete commands are run from Python.

#### Implementation

Add [confirmation prompts](http://click.pocoo.org/5/prompts/#confirmation-prompts) with Click.

#### Pros
- Syntax is in keeping with Unix standards (e.g. `yum install`)

#### Cons
