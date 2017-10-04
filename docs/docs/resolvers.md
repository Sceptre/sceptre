---
layout: docs
---

# Resolvers

Sceptre implements resolvers, which can be used to resolve a value of a CloudFormation `parameter` or `sceptre_user_data` value at runtime. This is most commonly used to chain the outputs of one stack to the inputs of another.

If required, users can create their own resolvers, as described in the section on [Custom Resolvers](#custom-resolvers).

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

Fetches the value of an output from a different stack controlled by Sceptre.

Syntax:

```yaml
parameters | sceptre_user_data:
    <name>: !stack_output <stack_name>::<output_name>
```

Example:

```
parameters:
    VpcIdParameter: !stack_output shared/vpc::VpcIdOutput
```


Sceptre infers that the stack to fetch the output value from is a dependency, and builds that stack before the current one.
This resolver will add a dependency for the stack in which needs the output from.

### stack\_output\_external

Fetches the value of an output from a different stack in the same account and region.

If the stack whose output is being fetched is in the same environment, the basename of that stack can be used.

Syntax:

```yaml
parameters/sceptre_user_data:
    <name>: !stack_output_external <full_stack_name>::<output_name>
```

Example:

```yaml
parameters:
    VpcIdParameter: !stack_output_external prj-network-vpc::VpcIdOutput
```


### project_variables

<div class="alert alert-warning">
The project_variables resolver has been deprecated, and will be removed in a later version of Sceptre. Depending on your use case, you may find <a href="{{ site.baseurl }}/docs/environment_config.html#var">User Variables</a> appropriate.
</div>

Keys through the YAML object stored at `/path/to/file.yaml` with the segments of the stack name.

Syntax:

```yaml
parameters | sceptre_user_data:
    <name>: !project_variables /path/to/file.yaml
```

For example, given the stack `dev/vpc`, and the following file (`/my_config_file.yaml`):

```yaml
dev:
    vpc:
        Name: my_vpc
```

The resolver will return the dictionary `{"Name": "my_vpc"}`.

Example (`config/dev/vpc.yaml`):

```yaml
parameters:
    Tag: !project_variables /my_config_file.yaml
```

## Custom Resolvers

Users can define their own resolvers which are used by Sceptre to resolve the value of a parameter before it is passed to the CloudFormation template.

A resolver is a Python class which inherits from abstract base class `Resolver` found in the `sceptre.resolvers module`.

Resolvers are require to implement a `resolve()` function that takes no parameters and to call the base class initializer on initialisation.

Resolvers may have access to `argument`,  `stack_config`, `environment_config` and `connection_manager` as an attribute of `self`. For example `self.stack_config`.

This class should be defined in a file which is located at:

```
<sceptre_dir>/resolvers/<your resolver>.py
```

An arbitrary file name may be used as it is not checked by Sceptre.

The following python module template can be copied and used:


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

        self.argument is available from the base class and contains the
        argument defined in the sceptre config file (see below)

        The following attributes may be available from the base class:
        self.stack_config  (A dict of data from <stack_name>.yaml)
        self.environment_config  (A dict of data from config.yaml)
        self.connection_manager (A connection_manager)
        """
        return self.argument
```

This resolver can be used in a stack config file with the following syntax:

```yaml
template_path: <...>
parameters:
    # <your resolver name> is the lower camel-case version of your class name,
    # e.g `custom_resolver` <value> will be passed to the resolver's resolve()
    # method.
    param1: !<your_resolver_name> <value>
```
