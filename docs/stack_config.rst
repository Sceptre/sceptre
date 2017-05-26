.. highlight:: shell

============
Stack Config
============

Stack config stores config related to a particular stack, such as the path to that stack's template, and any parameters that stack may require.

Structure
---------

A stack config file is a yaml object of key-value pairs configuring a particular stack. The available keys are listed below.

- `dependencies`_ *(optional)*
- `hooks`_ *(optional)*
- `parameters`_ *(optional)*
- `protect`_ *(optional)*
- `sceptre_user_data`_ *(optional)*
- `stack_name`_ *(optional)*
- `stack_tags`_ *(optional)*
- `role_arn`_ *(optional)*
- `template_path`_ *(required)*

Sceptre only checks for and uses the above keys in stack config files, but any others added by the user are read in and are made available to the user via the ``sceptre.stack.Stack().config`` attribute.


``dependencies``
````````````````

A list of other stacks in the environment that this stack depends on. Note that if a stack fetches an output value from another stack using the ``stack_output`` resolver, that stack is automatically added as a dependency, and that stack need not be added as an explicit dependency here.

``hooks``
`````````

A list of arbitrary shell or python commands or scripts to run. Find out more in the `Hook`_ section.

``parameters``
``````````````

.. warning:: Sensitive data such as passwords or secret keys should not be stored in plaintext in stack config files. Instead, they should be passed in from the CLI using :ref:`templating`, or set via an environment variable with the `environment_variable`_ resolver.

A dictionary of key-value pairs to be supplied to a CloudFormation or Troposphere template as parameters. The keys must match up with the name of the parameter, and the value must be of the type as defined in the template. Note that Boto3 throws an exception if parameters are supplied to a template that are not required by that template. Resolvers can be used to add functionality to this key. Find out more in the `Resolvers`_ section.

A parameter can be specified either as a single value/resolver or a list of values/resolvers. Lists of values/resolvers will be formatted into an AWS compatible comma separated string e.g. ``value1,value2,value3``. Lists can contain a mixture of values and resolvers.

Syntax:

.. code-block:: yaml

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

Example:

.. code-block:: yaml

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

``protect``
```````````

Stack protection against execution of the following commands:

- ``launch-stack``
- ``create-stack``
- ``update-stack``
- ``delete-stack``
- ``execute-change-set``

``sceptre_user_data``
`````````````````````

A dictionary of arbitrary key-value pairs to be passed to a global variable named SCEPTRE_USER_DATA in a Troposphere template. Find out more in the `Sceptre User Data`_ section.

``stack_name``
``````````````

A custom name name to use instead of the Sceptre default.

.. warning:: Outputs from stacks with custom names can't be resolved using the standard `stack_output`_ resolver. Outputs should be resolved using the `stack_output_external`_ resolver. An explicit dependency should be added, using the  `dependencies`_ parameter, to make sure the stacks are launched in the correct order.

  e.g::

    parameters:
      VpcID: !stack_output_external <custom-named-vpc-stack>::VpcID
    dependencies:
      - <environment>/<stack>

``stack_tags``
``````````````

A dictionary of Tags to be applied to the stack.

``role_arn``
````````````

The ARN of a `CloudFormation Service Role <http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html>`_ that is assumed by CloudFormation to create, update or delete resources.

``template_path``
`````````````````

The path to the CloudFormation or Troposphere template to build the stack from. The path can either be absolute or relative to the Sceptre Directory. Whether Sceptre treats the template as CloudFormation or Troposphere depends on the template's file extension. Templates with ``.json`` or ``.yaml`` extensions will be treated as CloudFormation templates whereas files with ``.py`` extension will be treated as Troposphere. Note that the template filename may be different from the stack config filename.


Cascading Config
----------------

Stack config can be cascaded in the same way Environment config can be, as described in the section in Environment Config on :ref:`cascading_config`.


Templating
----------

Stack config supports templating in the same way Environment config can be, as described in the section in Environment Config on :ref:`templating`.


Resolvers
---------

Sceptre implements resolvers, which can be used to resolve a value of a CloudFormation parameter or sceptre_user_data value at runtime. This is most commonly used to chain the outputs of one stack to the inputs of another.

If required, users can create their own resolvers, as described in the section :ref:`custom_resolvers`.

Syntax
``````
.. code-block:: yaml

  parameters:
    <parameter_name>: !<resolver_name> <resolver_value>

  sceptre_user_data:
    <name>: !<resolver_name> <resolver_value>


Available Resolvers
```````````````````

``environment_variable``
************************

Fetches the value from an environment variable.

Syntax:

.. code-block:: yaml

    parameter|sceptre_user_data:
      <name>: !environment_variable ENVIRONMENT_VARIABLE_NAME

Example:

.. code-block:: yaml

    parameters:
      database_password: !environment_variable DATABASE_PASSWORD


``file_contents``
*****************

Reads in the contents of a file.

Syntax:

.. code-block:: yaml

    parameters|sceptre_user_data:
      <name>: !file_contents /path/to/file.txt

Example:

.. code-block:: yaml

    sceptre_user_data:
      iam_policy: !file_contents /path/to/policy.json


``stack_output``
****************

Fetches the value of an output from a different stack controlled by Sceptre.

Syntax:

.. code-block:: yaml

    parameters | sceptre_user_data:
      <name>: !stack_output <stack_name>::<output_name>

Example:

.. code-block:: yaml

    parameters:
      VpcIdParameter: !stack_output shared/vpc::VpcIdOutput


Sceptre infers that the stack to fetch the output value from is a dependency, and builds that stack before the current one.
This resolver will add a dependency for the stack in which needs the output from.

``stack_output_external``
*************************

Fetches the value of an output from a different stack in the same account and region.

If the stack whose output is being fetched is in the same environment, the basename of that stack can be used.

Syntax:

.. code-block:: yaml

    parameters/sceptre_user_data:
      <name>: !stack_output_external <full_stack_name>::<output_name>

Example:

.. code-block:: yaml

    parameters:
      VpcIdParameter: !stack_output_external prj-network-vpc::VpcIdOutput


``project_variables``
*********************

Keys through the YAML object stored at ``/path/to/file.yaml`` with the segments of the stack name.

Syntax:

.. code-block:: yaml

    parameters | sceptre_user_data:
      <name>: !project_variables /path/to/file.yaml

For example, given the stack ``dev/vpc``, and the following file (/my_config_file.yaml):

.. code-block:: yaml

    dev:
      vpc:
        Name: my_vpc

The resolver will return the dictionary ``{ "Name": "my_vpc" }``.

Example (config/dev/vpc.yaml):

.. code-block:: yaml

    parameters:
      Tag: !project_variables /my_config_file.yaml

.. warning:: The project_variables resolver has been deprecated, and will be removed in a later version of Sceptre. Depending on your use case, you may find user variables as seen on the :ref:`templating` section appropiate.

Environment Variables
---------------------

It is possible to replace values in stack config files with environment variables in two ways. For an explanation on why this is the case, see the FAQ on :ref:`two_envvars`

Sceptre User Data
-----------------

Troposphere templates can contain data which should be parameterised, but can't be parameterised using CloudFormation parameters. An example of this is if a Troposphere template which creates an IAM Role reads in the policy from a JSON file. The file path must be hardcoded in the Troposphere template.

Sceptre User Data allows users to store arbitrary key-value pairs in their ``<stack-name>.yaml`` file. This data is then passed as a Python dictionary to a global variable in the Troposphere template named ``SCEPTRE_USER_DATA``.

Syntax
``````
::

  sceptre_user_data:
    iam_policy_file_path: /path/to/policy.json

When compiled, the variable SCEPTRE_USER_DATA would be the dictionary ``{"iam_policy_file": "/path/to/policy.json"}``.

For Sceptre user data to work, the Troposphere template must also be modified, as specified in the section in Templates on :ref:`sceptre_user_data`.


Hook
----

Hooks allows the ability for custom commands to be run when Sceptre actions occur.

A hook is executed at a particular hook point when Sceptre is run.

If required, users can create their own ``hooks``, as described in the section :ref:`custom_hooks`.

Hook points
```````````

``before_create`` or ``after_create`` - run hook before or after stack creation.

``before_update`` or ``after_update`` - run hook before or after stack update.

``before_delete`` or ``after_delete`` - run hook before or after stack deletion.

.. warning:: ``before_launch`` and ``after_launch`` have been removed.


Syntax
``````
Hooks are specified in a stack's config file, using the following syntax::

  hooks:
    hook_point:
      - !command_type command 1
      - !command_type command 2


Available Hooks
```````````````

``bash``
********

Executes string as a bash command.

Syntax:

.. code-block:: yaml

    <hook_point>:
      - !bash <bash_command>

Example:

.. code-block:: yaml

    before_create:
      - !bash "echo hello"


``cmd``
********

Runs a command.

Syntax:

.. code-block:: yaml

    <hook_point>:
      - !cmd <command>

Example:

.. code-block:: yaml

    before_create:
      - !cmd "echo hello"


``asg_scheduled_actions``
*************************

Pauses or resumes autoscaling scheduled actions.

Syntax:

.. code-block:: yaml

    <hook_point>:
      - !asg_scheduled_actions "resume" | "suspend"

Example:

.. code-block:: yaml

    before_update:
      - !asg_scheduled_actions "suspend"


``asg_scaling_processes``
*************************

Suspends or resumes autoscaling scaling processes.

Syntax:

.. code-block:: yaml

    <hook_point>:
      - !asg_scaling_processes <suspend|resume>::<process-name>

Example:

.. code-block:: yaml

    before_update:
      - !asg_scaling_processes suspend::ScheduledActions

Full documentation on the suspend and resume processes:
http://docs.aws.amazon.com/autoscaling/latest/userguide/as-suspend-resume-processes.html

Hook Examples
`````````````

A stack's ``config.yml`` where multiple hooks with multiple commands are specified::

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


Examples
--------

.. code-block:: yaml

  template_path: templates/example.py
  parameters:
    param_1: value_1
    param_2: value_2

.. code-block:: yaml

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
