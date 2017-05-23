---
layout: docs
---

# Stack Config

Stack config stores config related to a particular stack, such as the path to that stack's template, and any parameters that stack may require.

## Structure

A stack config file is a yaml object of key-value pairs configuring a particular stack. The available keys are listed below.

- [dependencies](#dependencies) *(optional)*
- [hooks](#hooks) *(optional)*
- [parameters](#parameters) *(optional)*
- [protect](#protect) *(optional)*
- [sceptre_user_data](#sceptre_user_data) *(optional)*
- [stack_name](#stack_name) *(optional)*
- [stack_tags](#stack_tags) *(optional)*
- [role_arn](#role_arn) *(optional)*
- [template_path](#template_path) *(required)*


### dependencies

A list of other stacks in the environment that this stack depends on. Note that if a stack fetches an output value from another stack using the `stack_output` resolver, that stack is automatically added as a dependency, and that stack need not be added as an explicit dependency here.

### hooks

A list of arbitrary shell or python commands or scripts to run. Find out more in the [Hook](#hook) section.

### parameters

<div class="alert alert-danger">
<strong>Warning</strong>: Sensitive data such as passwords or secret keys should not be stored in plaintext in stack config files. Instead, they should be passed in from the CLI with <a href="/docs/environment_config#var">User Variables</a>, or set via an environment variable with the <a href="#environment_variable">environment variable resolver</a>.
</div>

A dictionary of key-value pairs to be supplied to a CloudFormation or Troposphere template as parameters. The keys must match up with the name of the parameter, and the value must be of the type as defined in the template. Note that Boto3 throws an exception if parameters are supplied to a template that are not required by that template. Resolvers can be used to add functionality to this key. Find out more in the [Resolvers](#resolvers) section.

A parameter can be specified either as a single value/resolver or a list of values/resolvers. Lists of values/resolvers will be formatted into an AWS compatible comma separated string e.g. `value1,value2,value3`. Lists can contain a mixture of values and resolvers.

Syntax:

```yaml
parameters:
    <parameter1_name>: "value"
    <parameter2_name>: !<resolver_name> <resolver_value>
    <parameter3_name>:
        - "value1"
        - "value2"
    <parameter4_name>:
        - !<resolver_name> <resolver_value>
        - !<resolver_name> <resolver_value>
    <parameter5_name>:
        - !<resolver_name> <resolver_value>
        - "value1"
```

Example:

```yaml
parameters:
    database_username: "mydbuser"
    database_password: !environment_variable DATABASE_PASSWORD
    subnet_ids:
        - "subnet-12345678"
        - "subnet-87654321"
    security_group_ids:
        - "sg-12345678"
        - !stack_output security-groups::BaseSecurityGroupId
        - !file_contents /file/with/security_group_id.txt
```

### protect

Stack protection against execution of the following commands:

- `launch-stack`
- `create-stack`
- `update-stack`
- `delete-stack`
- `execute-change-set`

If a user tries to run one of these commands on a protected stack, Sceptre will throw an error.

### sceptre\_user\_data

A dictionary of arbitrary key-value pairs to be passed to the `sceptre_handler(sceptre_user_data)` function in Troposphere templates.

### stack_name

A custom name name to use instead of the Sceptre default.

<div class="alert alert-danger">
<strong>Warning</strong>: Outputs from stacks with custom names can't be resolved using the standard <a href="#stack_output">stack output resolver</a>. Outputs should be resolved using the <a href="#stack_output_external">stack output external resolver</a>. An explicit dependency should be added, using the <a href="#dependencies">dependencies</a> parameter, to make sure the stacks are launched in the correct order.
</div>

e.g:

```yaml
parameters:
    VpcID: !stack_output_external <custom-named-vpc-stack>::VpcID
dependencies:
    - <environment>/<stack>
```

### stack_tags

A dictionary of [CloudFormation Tags](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_Tag.html) to be applied to the stack.

### role_arn

The ARN of a [CloudFormation Service Role](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html) that is assumed by CloudFormation to create, update or delete resources.

### template_path

The path to the CloudFormation or Troposphere template to build the stack from. The path can either be absolute or relative to the Sceptre Directory. Whether Sceptre treats the template as CloudFormation or Troposphere depends on the template's file extension. Templates with `.json` or `.yaml` extensions will be treated as CloudFormation templates whereas files with `.py` extension will be treated as Troposphere. Note that the template filename may be different from the stack config filename.


## Cascading Config

Stack config can be cascaded in the same way Environment config can be, as described in the section in Environment Config on [Cascading Config](/docs/environment_config#cascading-config).


## Templating

Stack config supports templating in the same way Environment config can be, as described in the section in Environment Config on [Templating](/docs/environment_config#templating).


## Resolvers

Sceptre implements resolvers, which can be used to resolve a value of a CloudFormation `parameter` or `sceptre_user_data` value at runtime. This is most commonly used to chain the outputs of one stack to the inputs of another.

If required, users can create their own resolvers, as described in the section on [Custom Resolvers](/docs/advanced_patterns#custom-resolvers).

### Syntax

```yaml
parameters:
    <parameter_name>: !<resolver_name> <resolver_value>
sceptre_user_data:
    <name>: !<resolver_name> <resolver_value>
```


### Available Resolvers

#### environment_variable

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


#### file_contents

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

#### stack_output

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

#### stack\_output\_external

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


#### project_variables

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


Environment Variables
---------------------

It is possible to replace values in stack config files with environment variables in two ways. For an explanation on why this is the case, see the [FAQ](/docs/faq#why-are-there-two-ways-to-supply-environment-variables-in-stack-config-files).

## Sceptre User Data

Troposphere templates can contain data which should be parameterised, but can't be parameterised using CloudFormation parameters. An example of this is if a Troposphere template which creates an IAM Role reads in the policy from a JSON file. The file path must be hardcoded in the Troposphere template.

Sceptre user data allows users to store arbitrary key-value pairs in their `<stack-name>.yaml` file. This data is then passed as a Python `dict` to the `sceptre_handler(sceptre_user_data)` function in Troposphere templates.

### Syntax

```yaml
sceptre_user_data:
    iam_policy_file_path: /path/to/policy.json
```

When compiled, `sceptre_user_data` would be the dictionary `{"iam_policy_file": "/path/to/policy.json"}`.


## Hook

Hooks allows the ability for custom commands to be run when Sceptre actions occur.

A hook is executed at a particular hook point when Sceptre is run.

If required, users can create their own `hooks`, as described in the section [Custom Hooks](/docs/advanced_patterns#custom-hooks).


### Hook points

`before_create` or `after_create` - run hook before or after stack creation.

`before_update` or `after_update` - run hook before or after stack update.

`before_delete` or `after_delete` - run hook before or after stack deletion.


### Syntax

Hooks are specified in a stack's config file, using the following syntax::

```yaml
hooks:
    hook_point:
        - !command_type command 1
        - !command_type command 2
```


### Available Hooks

#### bash

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


#### asg\_scheduled\_actions

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


#### asg\_scaling_processes

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


#### Hook Examples

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


## Examples

```yaml
template_path: templates/example.py
parameters:
    param_1: value_1
    param_2: value_2
```

```yaml
template_path: templates/example.json
dependencies:
    - vpc
hooks:
    before_create:
        - !bash "echo creating..."
    after_create:
        - !bash "echo created"
        - !bash "echo done"
    after_update:
        - !bash "mkdir example"
        - !bash "touch example.txt"
parameters:
    param_1: !stack_output stack_name::output_name
    param_2: !stack_output_external full_stack_name::output_name
    param_3: !environment_variable VALUE_3
    param_4:
        {{ var.value4 }}
    param_5:
        {{ environment_path.3 }}
    param_6:
        {{ environment_variable.VALUE_6 }}
sceptre_user_data:
    thing_1: value_1
    thing_2: !file_contents path/to/file.txt
stack_tags:
    tag_1: value_1
    tag_2: value_2
```

