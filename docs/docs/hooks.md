---
layout: docs
---

# Hooks

Hooks allows the ability for custom commands to be run when Sceptre actions occur.

A hook is executed at a particular hook point when Sceptre is run.

If required, users can create their own `hooks`, as described in the section [Custom Hooks](#custom-hooks).


## Hook points

`before_create` or `after_create` - run hook before or after stack creation.

`before_update` or `after_update` - run hook before or after stack update.

`before_delete` or `after_delete` - run hook before or after stack deletion.


Syntax:

Hooks are specified in a stack's config file, using the following syntax:

```yaml
hooks:
    hook_point:
        - !command_type command 1
        - !command_type command 2
```


## Available Hooks

### cmd
Executes the argument string in the shell as a Python subprocess.

For more information about how this works, see the [subprocess documentation](https://docs.python.org/2/library/subprocess.html)

Syntax:

```yaml
<hook_point>:
    - !cmd <shell_command>
```

Example:

```yaml
before_create:
    - !cmd "echo hello"
```


### bash

<div class="alert alert-warning">
The bash hook has been deprecated, and will be removed in a later version of Sceptre. We recommend using the cmd hook instead.
</div>
Executes string as a bash command.

Syntax:

```yaml
<hook_point>:
    - !bash <bash_command>
```

Example:

```yaml
before_create:
    - !bash "echo hello"
```


### asg\_scheduled\_actions

<div class="alert alert-warning">
The asg_scheduled_actions hook has been deprecated and will be removed in a later version of Sceptre. We recommend using the asg_scaling_processes hook instead.
</div>
Pauses or resumes autoscaling scheduled actions.

Syntax:

```yaml
<hook_point>:
    - !asg_scheduled_actions "resume | suspend"
```

Example:

```yaml
before_update:
    - !asg_scheduled_actions "suspend"
```


### asg\_scaling_processes

Suspends or resumes autoscaling scaling processes.

Syntax:

```yaml
<hook_point>:
    - !asg_scaling_processes <suspend|resume>::<process-name>
```

Example:

```yaml
before_update:
    - !asg_scaling_processes suspend::ScheduledActions
```

More information on suspend and resume processes can be found in the AWS [documentation](http://docs.aws.amazon.com/autoscaling/latest/userguide/as-suspend-resume-processes.html).


## Examples

A stack's `config.yml` where multiple hooks with multiple commands are specified:

```yaml
template_path: templates/example.py
parameters:
    ExampleParameter: example_value
hooks:
    before_create:
        - !bash "echo creating..."
    after_create:
        - !bash "echo created"
        - !bash "echo done"
    before_update:
        - !asg_scheduled_actions suspend
    after_update:
        - !bash "mkdir example"
        - !bash "touch example.txt"
        - !asg_scheduled_actions resume
```

## Custom Hooks

Users can define their own custom hooks, allowing users to extend hooks and integrate additional functionality into Sceptre projects.

A hook is a Python class which inherits from abstract base class `Hook` found in the `sceptre.hooks module`.

Hooks are require to implement a `run()` function that takes no parameters and to call the base class initializer on initialisation.

Hooks may have access to `argument`,  `stack_config`, `environment_config` and `connection_manager` as an attribute of `self`. For example `self.stack_config`.

Hook classes are defined in python files located at:

```
<sceptre_project_dir>/hooks/<your hook>.py
```

Sceptre retrieves any class which inherits from base class Hook found within this directory. The name of the hook is the class name in snake case format. e.g. `class CustomHook` is `custom_hook`.  An arbitrary file name may be used as it is not checked by Sceptre.

The following python module template can be copied and used:

```python
from sceptre.hooks import Hook


class CustomHook(Hook):

    def __init__(self, *args, **kwargs):
        super(CustomHook, self).__init__(*args, **kwargs)

    def run(self):
        """
        run is the method called by Sceptre. It should carry out the work
        intended by this hook.

        self.argument is available from the base class and contains the
        argument defined in the sceptre config file (see below)

        The following attributes may be available from the base class:
        self.stack_config  (A dict of data from <stack_name>.yaml)
        self.environment_config  (A dict of data from config.yaml)
        self.connection_manager (A connection_manager)
        """
        print self.argument
```


This hook can be used in a stack config file with the following syntax:

```yaml
template_path: <...>
hooks:
    before_create:
        - !custom_hook <argument>  # The argument is accessible via self.argument
```
