Stack Config
============

A Stack config stores configurations related to a particular Stack, such as the path to
that Stack’s Template, and any parameters that Stack may require. Many of these configuration keys
support resolvers and can be inherited from parent StackGroup configs.

.. _stack_config-structure:

Structure
---------

A Stack config file is a ``yaml`` object of key-value pairs configuring a
particular Stack. The available keys are listed below.

-  `template_path`_ or `template`_ *(required)*
-  `dependencies`_ *(optional)*
-  `dependencies_inheritance`_ *(optional)*
-  `hooks`_ *(optional)*
-  `hooks_inheritance`_ *(optional)*
-  `ignore`_ *(optional)*
-  `notifications`_ *(optional)*
-  `obsolete`_ *(optional)*
-  `on_failure`_ *(optional)*
-  `disable_rollback`_ *(optional)*
-  `parameters`_ *(optional)*
-  `parameters_inheritance`_ *(optional)*
-  `protected`_ *(optional)*
-  `role_arn`_ *(optional)*
-  `cloudformation_service_role`_ *(optional)*
-  `iam_role`_ *(optional)*
-  `sceptre_role`_ (*optional)*
-  `iam_role_session_duration`_ *(optional)*
-  `sceptre_role_session_duration`_ *(optional)*
-  `sceptre_user_data`_ *(optional)*
-  `sceptre_user_data_inheritance`_ *(optional)*
-  `stack_name`_ *(optional)*
-  `stack_tags`_ *(optional)*
-  `stack_tags_inheritance`_ *(optional)*
-  `stack_timeout`_ *(optional)*

It is not possible to define both `template_path`_ and `template`_. If you do so,
you will receive an error when deploying the stack.

template_path
~~~~~~~~~~~~~~~~~~~~~~~~
* Resolvable: No
* Can be inherited from StackGroup: No

The path to the CloudFormation, Jinja2 or Python template to build the Stack
from. The path can either be absolute or relative to the Sceptre Directory.
Sceptre treats the template as CloudFormation, Jinja2 or Python depending on
the template’s file extension. Note that the template filename may be different
from the Stack config filename.

.. warning::

   This key is deprecated in favor of the `template`_ key. It will be removed in version 5.0.0.

template
~~~~~~~~
* Resolvable: Yes
* Can be inherited from StackGroup: No

Configuration for a template handler. Template handlers can take in parameters
and resolve that to a CloudFormation template. This enables you to not only
load templates from disk, but also from third-party storage or AWS services.

Example for loading from S3 bucket:

.. code-block:: yaml

   template:
     type: s3
     path: infra-templates/s3/v1/bucket.yaml
   parameters:
     <parameter1_name>: "value"
   sceptre_user_data:

It is possible to write your own template handlers should you need to. You
can find a list of currently supported template handlers and guidance for
developing your own in the :doc:`template_handlers` section.

dependencies
~~~~~~~~~~~~
* Resolvable: No
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Appended to parent's dependencies. Configurable with ``dependencies_inheritance`` parameter.

A list of other Stacks in the environment that this Stack depends on. Note that
if a Stack fetches an output value from another Stack using the
``stack_output`` resolver, that Stack is automatically added as a dependency,
and that Stack need not be added as an explicit dependency.

.. warning::
   Be careful about how you structure dependencies. It is possible to create circular
   dependencies accidentally, where multiple stacks depend on each other. Sceptre
   will detect this and raise an error, blocking this sort of setup. You must be especially careful
   when specifying ``dependencies`` on a StackGroup config. These dependencies will then be
   "inherited" by every stack within that StackGroup. If one of those dependencies *inherits* that
   list of dependencies, it will cause a circular dependency. If this happens, you can resolve the
   situation by either (a) setting those ``dependencies`` on individual Stack Configs rather than the
   the StackGroup Config, or (b) moving those dependency stacks outside of the StackGroup.

dependencies_inheritance
~~~~~~~~~~~~~~~~~~~~~~~~
* Resolvable: No
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Overrides parent if set

This configuration will override the default inheritance strategy of `dependencies`.

The default value for this is ``merge``.

Valid values for this config are: ``merge``, or ``override``.

hooks
~~~~~
* Resolvable: No (but you can use resolvers _in_ hook arguments!)
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Overrides parent if set. Configurable with ``hooks_inheritance`` parameter.

A list of arbitrary shell or Python commands or scripts to run. Find out more
in the :doc:`hooks` section.

hooks_inheritance
~~~~~~~~~~~~~~~~~~~~~~~~
* Resolvable: No
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Overrides parent if set

This configuration will override the default inheritance strategy of `hooks`.

The default value for this is ``override``.

Valid values for this config are: ``merge``, or ``override``.

ignore
~~~~~~
* Resolvable: No
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Overrides parent if set

This configuration should be set with a boolean value of ``True`` or ``False``. By default, this is
set to ``False`` on all stacks.

``ignore`` determines how the stack should be handled when running ``sceptre launch``. A stack
marked with ``ignore: True`` will be completely ignored by the launch command. If the stack does NOT
exist on AWS, it won't be created. If it *DOES* exist, it will neither be updated nor deleted.

You *can* mark a stack with ``ignore: True`` that other non-ignored stacks depend on, but the launch
will fail if dependent stacks require resources or outputs that don't exist because the stack has not been
launched. **Therefore, only ignore dependencies of other stacks if you are aware of the risks of
launch failure.**

This setting can be especially useful when combined with Jinja logic to exclude certain stacks from
launch based upon conditional Jinja-based template logic.

For Example:

.. code-block:: yaml

   template:
       path: "my/test/resources.yaml"

   # Configured this way, if the var "use_test_resources" is not true, the stack will not be launched
   # and instead excluded from the launch. But if "use_test_resources" is true, the stack will be
   # deployed along with the rest of the resources being deployed.
   {% if not var.use_test_resources %}
   ignore: True
   {% endif %}


.. note::
   The ``ignore`` configuration **only** applies to the **launch** command. You can still run
   ``create``, ``update``, or ``delete`` commands on a stack marked with ``ignore: True``;
   these commands will ignore the ``ignore`` setting and act upon the stack the same as any other.

notifications
~~~~~~~~~~~~~
* Resolvable: Yes
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Overrides parent if set

List of SNS topic ARNs to publish Stack related events to. A maximum of 5 ARNs
can be specified per Stack. This configuration will be used by the ``create``,
``update``, or ``delete`` commands. More information about Stack notifications
can found under the relevant section in the `AWS CloudFormation API
documentation`_.

.. _`obsolete`:

obsolete
~~~~~~~~
* Resolvable: No
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Overrides parent if set

This configuration should be set with a boolean value of ``True`` or ``False``. By default, this is
set to ``False`` on all stacks.

The ``obsolete`` configuration should be used to mark stacks to be deleted via ``prune`` actions,
if they currently exist on AWS. (If they don't exist on AWS, pruning does nothing).

There are two ways to prune obsolete stacks:

1. ``sceptre prune`` will delete *all* obsolete stacks in the **project**.
2. ``sceptre launch --prune [command path]`` will delete all obsolete stacks in the command path
   before continuing with the launch.

In practice, the ``obsolete`` configuration operates identically to ``ignore`` with the extra prune
effects. When the ``launch`` command is invoked without the ``--prune`` flag, obsolete stacks will
be ignored and not launched, just as if ``ignore: True`` was on the Stack Config.

**Important**: You cannot have non-obsolete stacks dependent upon obsolete stacks. Both the
``prune`` and ``launch --prune`` will reject such configurations and will not continue if this sort
of dependency structure is detected. Only obsolete stacks can depend on obsolete stacks.

.. note::
   The ``obsolete`` configuration **only** applies to the **launch** and **prune** commands. You can
   still run ``create``, ``update``, or ``delete`` commands on a stack marked with ``obsolete: True``;
   these commands will ignore the ``obsolete`` setting and act upon the stack the same as any other.

on_failure
~~~~~~~~~~
* Resolvable: No
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Overrides parent if set

This parameter describes the action taken by CloudFormation when a Stack fails
to create. For more information and valid values see the `AWS Documentation`_.

Examples include:

``on_failure: "DO_NOTHING"``

``on_failure: "ROLLBACK"``

``on_failure: "DELETE"``

disable_rollback
~~~~~~~~~~~~~~~~
* Resolvable: No
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Overrides parent if set

This parameter describes the action taken by CloudFormation when a Stack fails
to create or update, default is False. This option can be set from the stack
config or from the Sceptre CLI commands to deploy stacks. The disable_rollback
CLI option (i.e. sceptre launch --disable-rollback) disables cloudformation
rollback globally for all stacks. This option overrides on_failure since
Cloudformation does not allow setting both on deployment. For more information
and valid values see the `AWS Documentation`_.

Examples:

``disable_rollback: "True"``

parameters
~~~~~~~~~~
* Resolvable: Yes
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Overrides parent if set. Configurable with ``parameters_inheritance`` parameter.

.. warning::

   Sensitive data such as passwords or secret keys should not be stored in
   plaintext in Stack config files. Instead, they should be passed in from the
   CLI with User Variables, or set via an environment variable with the
   environment variable resolver.

A dictionary of key-value pairs to be supplied to a template as parameters. The
keys must match up with the name of the parameter, or the value must be of the
type as defined in the template.

.. note::

   Note that Boto3 throws an exception if parameters are supplied to a template
   that are not required by that template. Resolvers can be used to add
   functionality to this key. Find out more in the :doc:`resolvers` section.

.. warning::

   In case the same parameter key is supplied more than once, the last
   definition silently overrides the earlier definitions.

A parameter can be specified either as a single value/resolver or a list of
values/resolvers. Lists of values/resolvers will be formatted into an AWS
compatible comma separated string e.g. \ ``value1,value2,value3``. Lists can
contain a mixture of values and resolvers.

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
       - !stack_output security-groups.yaml::BaseSecurityGroupId
       - !file_contents /file/with/security_group_id.txt

parameters_inheritance
~~~~~~~~~~~~~~~~~~~~~~~~
* Resolvable: No
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Overrides parent if set

This configuration will override the default inheritance strategy of `parameters`.

The default value for this is ``override``.

Valid values for this config are: ``merge``, or ``override``.

protected
~~~~~~~~~
* Resolvable: No
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Overrides parent if set

Stack protection against execution of the following commands:

-  ``launch``
-  ``create``
-  ``update``
-  ``delete``
-  ``execute``

If a user tries to run one of these commands on a protected Stack, Sceptre will
throw an error.

role_arn
~~~~~~~~
* Resolvable: Yes
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Overrides parent if set

.. warning::
   This field is deprecated as of v4.0.0 and will be removed in v5.0.0. It has been renamed to
   `cloudformation_service_role`_ as a clearer name for its purpose.

cloudformation_service_role
~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Resolvable: Yes
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Overrides parent if set

The ARN of a `CloudFormation Service Role`_ that is assumed by *CloudFormation* (not Sceptre)
to create, update or delete resources. For more information on this configuration, its implications,
and its uses see :ref:`Sceptre and IAM: cloudformation_service_role <cloudformation_service_role_permissions>`.

iam_role
~~~~~~~~
* Resolvable: Yes
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Overrides parent if set

.. warning::
   This field is deprecated as of v4.0.0 and will be removed in v5.0.0. It has been renamed to
   `sceptre_role`_ as a clearer name for its purpose.

sceptre_role
~~~~~~~~~~~~
* Resolvable: Yes
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Overrides parent if set

This is the IAM Role ARN that **Sceptre** should *assume* using AWS STS when executing any actions
on the Stack.

This is different from the ``cloudformation_service_role`` option, which sets a CloudFormation
service role for the stack. The ``sceptre_role`` configuration does not configure anything on the
stack itself.

.. warning::

   If you set the value of ``sceptre_role`` with ``!stack_output``, that ``sceptre_role``
   will not actually be used to obtain the stack_output, but it *WILL* be used for all subsequent stack
   actions. Therefore, it is important that the user executing the stack action have permissions to get
   stack outputs for the stack outputting the ``sceptre_role``.

For more information on this configuration, its implications, and its uses, see
:ref:`Sceptre and IAM: sceptre_role <sceptre_role_permissions>`.

iam_role_session_duration
~~~~~~~~~~~~~~~~~~~~~~~~~
* Resolvable: No
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Overrides parent if set

.. warning::
   This field is deprecated as of v4.0.0 and will be removed in v5.0.0. It has been renamed to
   `sceptre_role_session_duration`_ as a clearer name for its purpose.

sceptre_role_session_duration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Resolvable: No
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Overrides parent if set

This is the session duration when **Sceptre** *assumes* the **sceptre_role** IAM Role using AWS STS when
executing any actions on the Stack.

.. warning::

   If you set the value of ``sceptre_role_session_duration`` to a number that *GREATER* than 3600, you
   will need to make sure that the ``sceptre_role`` has a configuration of ``MaxSessionDuration``, and
   its value is *GREATER* than or equal to the value of ``sceptre_role_session_duration``.

sceptre_user_data
~~~~~~~~~~~~~~~~~
* Resolvable: Yes
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Overrides parent if set. Configurable with ``sceptre_user_data_inheritance`` parameter.

Represents data to be passed to the ``sceptre_handler(sceptre_user_data)``
function in Python templates or accessible under ``sceptre_user_data`` variable
key within Jinja2 templates.

sceptre_user_data_inheritance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Resolvable: No
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Overrides parent if set

This configuration will override the default inheritance strategy of `sceptre_user_data`.

The default value for this is ``override``.

Valid values for this config are: ``merge``, or ``override``.

stack_name
~~~~~~~~~~
* Resolvable: No
* Can be inherited from StackGroup: No

A custom name to use instead of the Sceptre default.

.. container:: alert alert-warning

   Outputs from Stacks with custom names can’t be resolved using the standard
   stack output resolver. Outputs should be resolved using the stack output
   external resolver. An explicit dependency should be added, using the
   dependencies parameter, to make sure the Stacks are launched in the correct
   order.

e.g:

.. code-block:: yaml

   parameters:
     VpcID: !stack_output_external <custom-named-vpc-stack>::VpcID
   dependencies:
     - <environment>/<Stack>

You can also pass an optional argument to ``stack_output_external`` specifying
the profile you want to use. This is especially useful if the Template you’re
referring to is in a different AWS account or region.

.. code-block:: yaml

   parameters:
     VpcID: !stack_output_external <custom-named-vpc-stack>::VpcID my-aws-prod-profile
   dependencies:
     - <environment>/<Stack>

stack_tags
~~~~~~~~~~
* Resolvable: Yes
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Overrides parent if set. Configurable with ``stack_tags_inheritance`` parameter.

A dictionary of `CloudFormation Tags`_ to be applied to the Stack.

stack_tags_inheritance
~~~~~~~~~~~~~~~~~~~~~~~~
* Resolvable: No
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Overrides parent if set

This configuration will override the default inheritance strategy of `stack_tags`.

The default value for this is ``override``.

Valid values for this config are: ``merge``, or ``override``.

stack_timeout
~~~~~~~~~~~~~
* Resolvable: No
* Can be inherited from StackGroup: Yes
* Inheritance strategy: Overrides parent if set

A timeout in minutes before considering the Stack deployment as failed. After
the specified timeout, the Stack will be rolled back. Specifiyng zero, as well
as ommiting the field, will result in no timeout. Supports only positive
integer value.

Cascading Config
----------------

Stack config can be cascaded in the same way StackGroup config can be, as
described in the section in StackGroup Config on
:ref:`Cascading Config <stack_group_config_cascading_config>`.


Templating
----------

Stack config supports templating in the same way StackGroup config can be, as
described in the section in StackGroup Config on :ref:`Templating <stack_group_config_templating>`.

Stack config makes StackGroup config available to template.

StackGroup config
~~~~~~~~~~~~~~~~~

StackGroup config properties are available via the stack_group_config variable
when using templating.

.. code-block:: yaml

   parameters:
     sceptre-project-code: {{ stack_group_config.project-code }}

Environment Variables
---------------------

It is possible to replace values in Stack config files with environment
variables in two ways. For an explanation on why this is the case, see the
:ref:`FAQ <faq_stackconfig_env>`.

Sceptre User Data
-----------------

Python or Jinja templates can contain data which should be parameterised, but
can’t be parameterised using CloudFormation parameters. An example of this is
if a Python template which creates an IAM Role reads in the policy from a JSON
file. The file path must be hard-coded in the Python template.

Sceptre user data allows users to store arbitrary key-value pairs in their
``<stack-name>.yaml`` file. This data is then passed as a Python ``dict`` to
the ``sceptre_handler(sceptre_user_data)`` function in Python templates.

Syntax:

.. code-block:: yaml

   sceptre_user_data:
     iam_policy_file_path: /path/to/policy.json

When compiled, ``sceptre_user_data`` would be the dictionary
``{"iam_policy_file": "/path/to/policy.json"}``.

.. _resolution_order:

Resolution order of values
--------------------------

Stack Configs allow you to pull together values from a variety of sources to configure a
CloudFormation stack. These values are retrieved and applied in phases. Understanding these phases can
be very helpful when designing your Stack Configs.

When launching a stack (or performing other stack actions), values are gathered and accessed in this
order:

1. User variables (from ``--var`` and ``--var-file`` arguments) are gathered when the CLI first runs.
2. StackGroup Configs are read from the highest level downward, rendered with Jinja and then loaded
   into yaml. The key/value pairs from these configs are layered on top of each other, with more nested
   configs overriding higher-level ones. These key/value pairs will be "inherited" by the Stack
   Config. These variables are made available when rendering a StackGroup Config:

   * User variables (via ``{{ var }}``)
   * Environment variables (via ``{{ environment_variable }}``)
   * StackGroup configurations from *higher* level StackGroup Configs are available by name. Note:
     more nested configuration values will overshadow higher-level ones by the same key.

3. With the layered StackGroup Config variables, the Stack Config file will be read and then rendered
   with Jinja. These variables are made available when the Stack Config is being rendered with Jinja:

   * User variables (via ``{{ var }}``)
   * Environment variables (via ``{{ environment_variable }}``)
   * All StackGroup configurations are available by name directly as well as via ``{{ stack_group_config }}``

   **Important:** If any StackGroup configuration values were set with resolvers, accessing them via
   Jinja will not resolve them, since resolvers require a Stack object, which has not yet been
   assembled yet. **Resolvers will not be accessible until a later phase.**
4. Once rendered via Jinja into a string, the Stack Config will be loaded into yaml. This is when the
   resolver instances on the Stack config will be **constructed** (*not* resolved).
5. The Stack instance will be constructed with the key/value pairs from the loaded yaml layered on
   top of the key/value pairs from the StackGroup configurations. This is when all resolver instances,
   both those inherited from StackGroup Configs and those from the present Stack Config, will be
   connected to the Stack instance and thus *ready* to be resolved.
6. The first time a resolvable configuration is *accessed* is when the resolver(s) at that
   configuration will be resolved and replaced with their resolved value. This is normally done at
   the very last moment, right when it is needed (and not before).

"Render Time" vs. "Resolve Time"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A common point of confusion tends to be around the distinction between **"render time"** (phase 3, when
Jinja logic is applied) and **"resolve time"** (phase 6, when resolvers are resolved). You cannot use
a resolver via Jinja during "render time", since the resolver won't exist or be ready to use yet. You can,
however, use Jinja logic to indicate *whether*, *which*, or *how* a resolver is configured. You can
also use resolvers like ``!sub`` to interpolate resolved values when Jinja isn't available.

For example, you **can** do something like this:

.. code-block:: yaml

   parameters:
     {% if var.use_my_parameter %}
       my_parameter: !stack_output {{ var.stack_name }}::{{ var.output_name }}
     {% endif %}
       # !sub will let you combine outputs of multiple resolvers into a single string
       my_combined_parameter: !sub
         - "{fist_part} - {second_part}"
         - first_part: !stack_output my/stack/name.yaml::Output
         - second_part: {{ var.second_part }}

Accessing resolved values in other fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes you might want to reference the resolved value of one field in another field. Since you cannot
use Jinja to access resolved values, there is another way to this. The :ref:`stack_attr_resolver`
resolver is meant for addressing just this need. It's a resolver that will resolve to the value of
another Stack Config field value. See the linked documentation for more details on that resolver and
its use.


Examples
--------

.. code-block:: yaml

   template:
     path: templates/example.py
     type: file
   parameters:
     param_1: value_1
     param_2: value_2

.. code-block:: yaml

   template:
     path: templates/example.yaml
     type: file
   dependencies:
       - dev/vpc.yaml
   hooks:
       before_create:
           - !cmd "echo creating..."
       after_create:
           - !cmd "echo created"
           - !cmd "echo done"
       after_update:
           - !cmd "mkdir example"
           - !cmd "touch example.txt"
   parameters:
       param_1: !stack_output stack_name.yaml::output_name
       param_2: !stack_output_external full_stack_name::output_name
       param_3: !environment_variable VALUE_3
       param_4:
           {{ var.value4 }}
       param_5:
           {{ command_path.3 }}
       param_6:
           {{ environment_variable.VALUE_6 }}
   sceptre_user_data:
       thing_1: value_1
       thing_2: !file_contents path/to/file.txt
   stack_tags:
       tag_1: value_1
       tag_2: value_2

.. _template_path: #template-path
.. _template: #template
.. _dependencies: #dependencies
.. _hooks: #hooks
.. _notifications: #notifications
.. _on_failure: #on-failure
.. _disable_rollback: #disable-rollback
.. _parameters: #parameters
.. _protected: #protected
.. _role_arn: #role-arn
.. _sceptre_user_data: #sceptre-user-data
.. _stack_name: #stack-name
.. _stack_tags: #stack-tags
.. _stack_timeout: #stack-timeout
.. _AWS CloudFormation API documentation: http://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_CreateStack.html
.. _AWS Documentation: http://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_CreateStack.html
.. _CloudFormation Service Role: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html
.. _CloudFormation Tags: https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_Tag.html
