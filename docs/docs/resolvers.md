---
layout: docs
title: Resolvers
---

# Resolvers

Sceptre implements resolvers, which can be used to resolve a value of
a CloudFormation `parameter` or `sceptre_user_data` value at runtime. This is
most commonly used to chain the outputs of one Stack to the inputs of another.

If required, users can create their own resolvers, as described in the section
on [Custom Resolvers](#custom-resolvers).

Syntax:

```yaml
parameters:
  <parameter_name>: !<resolver_name> <resolver_value>
sceptre_user_data:
  <name>: !<resolver_name> <resolver_value>
```

## Available Resolvers

### environment_variable

Fetches the value from an environment variable.

Syntax:

```yaml
parameter|sceptre_user_data:
  <name>: !environment_variable ENVIRONMENT_VARIABLE_NAME
```

Example:

```
parameters:
    database_password: !environment_variable DATABASE_PASSWORD
```

### file_contents

Reads in the contents of a file.

Syntax:

```yaml
parameters|sceptre_user_data:
  <name>: !file_contents /path/to/file.txt
```

Example:

```yaml
sceptre_user_data:
  iam_policy: !file_contents /path/to/policy.json
```

### stack_output

Fetches the value of an output from a different Stack controlled by Sceptre.

Syntax:

```yaml
parameters | sceptre_user_data:
  <name>: !stack_output <stack_name>.yaml::<output_name>
```

Example:

```
parameters:
    VpcIdParameter: !stack_output shared/vpc.yaml::VpcIdOutput
```

Sceptre infers that the Stack to fetch the output value from is a dependency,
and builds that Stack before the current one.

This resolver will add a dependency for the Stack in which needs the output
from.

### stack_output_external

Fetches the value of an output from a different Stack in the same account and
region.

If the Stack whose output is being fetched is in the same StackGroup, the
basename of that Stack can be used.

Syntax:

```yaml
parameters/sceptre_user_data:
  <name>: !stack_output_external <full_stack_name>::<output_name> <optional-aws-profile-name>
```

Example:

```yaml
parameters:
  VpcIdParameter: !stack_output_external prj-network-vpc::VpcIdOutput prod
```

## Custom Resolvers

Users can define their own resolvers which are used by Sceptre to resolve the
value of a parameter before it is passed to the CloudFormation template.

A resolver is a Python class which inherits from abstract base class `Resolver`
found in the `sceptre.resolvers module`.

Resolvers are require to implement a `resolve()` function that takes no
parameters and to call the base class initializer on initialisation.

Resolvers may have access to `argument`, `stack_config`, `stack_group_config`
and `connection_manager` as an attribute of `self`. For example
`self.stack_config`.

Sceptre uses the `sceptre.resolvers` entry point to locate resolver classes.
Your custom resolver can be written anywhere and is installed as Python
package.

### Example

The following python module template can be copied and used:

```bash
custom_resolver
├── custom_resolver.py
└── setup.py
```

The following python module template can be copied and used:

#### custom_resolver.py

```python
from sceptre.resolvers import Resolver

class CustomResolver(Resolver):

    def __init__(self, *args, **kwargs):
        super(CustomResolver, self).__init__(*args, **kwargs)

    def resolve(self):
        """
        resolve is the method called by Sceptre. It should carry out the work
        intended by this resolver. It should return a string to become the
        final value.

        The following parameters are available to Resolvers:

        :param argument: The argument of the resolver.
        :type argument: str
        :param stack: The associated stack of the resolver.
        :type stack: sceptre.stack.Stack
        """
        return self.argument
```

The resolver name is the lower snake-case version of the class name. The
argument of the resolver (`<value>`) will be available inside the resolver as
`self.argument`. The resolver subclass above can be used in a Stack config file
with the following syntax:

#### setup.py

```python
from setuptools import setup

setup(
    name='custom_resolver',
    py_modules=['<custom_resolver_name>'],
    entry_points={
        'sceptre.resolvers': [
            '<custom_resolver_name> = <custom_resolver_name>:CustomResolver',
        ],
    }
)
```

Then install using `python setup.py install` or `pip install .` commands.

This resolver can be used in a Stack config file with the following syntax:

```yaml
template_path: <...>
parameters:
  param1: !<your_resolver_name> <value> <optional-aws-profile>
```
