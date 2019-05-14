Stack Config
============

Stack config stores config related to a particular Stack, such as the path to
that Stack’s Template, and any parameters that Stack may require.

.. _stack_config-structure:

Structure
---------

A Stack config file is a ``yaml`` object of key-value pairs configuring a
particular Stack. The available keys are listed below.

-  `template_path`_ *(required)*
-  `dependencies`_ *(optional)*
-  `hooks`_ *(optional)*
-  `notifications`_ *(optional)*
-  `on_failure`_ *(optional)*
-  `parameters`_ *(optional)*
-  `protected`_ *(optional)*
-  `role_arn`_ *(optional)*
-  `sceptre_user_data`_ *(optional)*
-  `stack_name`_ *(optional)*
-  `stack_tags`_ *(optional)*
-  `stack_timeout`_ *(optional)*

template_path - required
~~~~~~~~~~~~~~~~~~~~~~~~

The path to the CloudFormation, Jinja2 or Python template to build the Stack
from. The path can either be absolute or relative to the Sceptre Directory.
Sceptre treats the template as CloudFormation, Jinja2 or Python depending on
the template’s file extension. Note that the template filename may be different
from the Stack config filename.

dependencies
~~~~~~~~~~~~

A list of other Stacks in the environment that this Stack depends on. Note that
if a Stack fetches an output value from another Stack using the
``stack_output`` resolver, that Stack is automatically added as a dependency,
and that Stack need not be added as an explicit dependency.

hooks
~~~~~

A list of arbitrary shell or Python commands or scripts to run. Find out more
in the :doc:`hooks` section.

notifications
~~~~~~~~~~~~~

List of SNS topic ARNs to publish Stack related events to. A maximum of 5 ARNs
can be specified per Stack. This configuration will be used by the ``create``,
``update``, and ``delete`` commands. More information about Stack notifications
can found under the relevant section in the `AWS CloudFormation API
documentation`_.

on_failure
~~~~~~~~~~

This parameter describes the action taken by CloudFormation when a Stack fails
to create. For more information and valid values see the `AWS Documentation`_.

parameters
~~~~~~~~~~

.. container:: alert alert-danger

   Sensitive data such as passwords or secret keys should not be stored in
   plaintext in Stack config files. Instead, they should be passed in from the
   CLI with User Variables, or set via an environment variable with the
   environment variable resolver.

A dictionary of key-value pairs to be supplied to a template as parameters. The
keys must match up with the name of the parameter, and the value must be of the
type as defined in the template.

   Note that Boto3 throws an exception if parameters are supplied to a template
   that are not required by that template. Resolvers can be used to add
   functionality to this key. Find out more in the :doc:`resolvers` section.

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
       - !stack_output security-groups::BaseSecurityGroupId
       - !file_contents /file/with/security_group_id.txt

protected
~~~~~~~~~

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

The ARN of a `CloudFormation Service Role`_ that is assumed by CloudFormation
to create, update or delete resources.

sceptre_user_data
~~~~~~~~~~~~~~~~~

Represents data to be passed to the ``sceptre_handler(sceptre_user_data)``
function in Python templates or accessible under ``sceptre_user_data`` variable
key within Jinja2 templates.

stack_name
~~~~~~~~~~

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
     VpcID: !stack_output_external <custom-named-vpc-stack>.yaml::VpcID
   dependencies:
     - <environment>/<Stack>

You can also pass an optional argument to ``stack_output_external`` specifying
the profile you want to use. This is especially useful if the Template you’re
referring to is in a different AWS account or region.

.. code-block:: yaml

   parameters:
     VpcID: !stack_output_external <custom-named-vpc-stack>.yaml::VpcID my-aws-prod-profile
   dependencies:
     - <environment>/<Stack>

stack_tags
~~~~~~~~~~

A dictionary of `CloudFormation Tags`_ to be applied to the Stack.

stack_timeout
~~~~~~~~~~~~~

A timeout in minutes before considering the Stack deployment as failed. After
the specified timeout, the Stack will be rolled back. Specifiyng zero, as well
as ommiting the field, will result in no timeout. Supports only positive
integer value.

Cascading Config
----------------

Stack config can be cascaded in the same way StackGroup config can be, as
described in the section in StackGroup Config on `Cascading Config`_.

Templating
----------

Stack config supports templating in the same way StackGroup config can be, as
described in the section in StackGroup Config on `Templating`_.

Stack config makes StackGroup config available to template.

StackGroup config
~~~~~~~~~~~~~~~~~

StackGroup config properties are available via the stack_group_config variable
when using templating.

.. code-block:: jinja

   parameters:
     sceptre-project-code: {% raw %}{{ stack_group_config.sceptre-project-code }}{% endraw %}

Environment Variables
---------------------

It is possible to replace values in Stack config files with environment
variables in two ways. For an explanation on why this is the case, see the
`FAQ`_.

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

Examples
--------

.. code-block:: yaml

   template_path: templates/example.py
   parameters:
     param_1: value_1
     param_2: value_2

.. code-block:: jinja

   {% raw %}
   template_path: example.json
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
       param_1: !stack_output stack_name::output_name
       param_2: !stack_output_external full_stack_name.yaml::output_name
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
   {% endraw %}

.. _template_path: #template_path
.. _dependencies: #dependencies
.. _hooks: #hooks
.. _notifications: #notifications
.. _on_failure: #on_failure
.. _parameters: #parameters
.. _protected: #protected
.. _role_arn: #role_arn
.. _sceptre_user_data: #sceptre_user_data
.. _stack_name: #stack_name
.. _stack_tags: #stack_tags
.. _stack_timeout: #stack_timeout
.. _AWS CloudFormation API documentation: http://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_CreateStack.html
.. _AWS Documentation: http://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_CreateStack.html
.. _CloudFormation Service Role: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html
.. _CloudFormation Tags: https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_Tag.html
.. _Cascading Config: %7B%7B%20site.baseurl%20%7D%7D/docs/stack_group_config.html#cascading-config
.. _Templating: %7B%7B%20site.baseurl%20%7D%7D/docs/stack_group_config.html#templating
.. _FAQ: %7B%7B%20site.baseurl%20%7D%7D/docs/faq.html#why-are-there-two-ways-to-supply-environment-variables-in-Stack-config-files
