Stack Config
============

Stack config stores config related to a particular stack, such as the
path to that stack's template, and any parameters that stack may
require.

Structure
---------

A stack config file is a yaml object of key-value pairs configuring a
particular stack. The available keys are listed below.

-  `dependencies`_ *(optional)*
-  `hooks`_ *(optional)*
-  `on\_failure`_ *(optional)*
-  `parameters`_ *(optional)*
-  `protect`_ *(optional)*
-  `sceptre\_user\_data`_ *(optional)*
-  `stack\_name`_ *(optional)*
-  `stack\_tags`_ *(optional)*
-  `role\_arn`_ *(optional)*
-  `notifications`_ *(optional)*
-  `template\_path`_ *(required)*
-  `stack\_timeout`_ *(optional)*

dependencies
~~~~~~~~~~~~

A list of other stacks in the environment that this stack depends on.
Note that if a stack fetches an output value from another stack using
the ``stack_output`` resolver, that stack is automatically added as a
dependency, and that stack need not be added as an explicit dependency
here.

hooks
~~~~~

A list of arbitrary shell or python commands or scripts to run. Find out
more in the :ref:`Hooks <Hooks>` section.

on\_failure
~~~~~~~~~~~

This parameter describes the action taken by CloudFormation when a stack
fails to create. For more information and valid values see the `AWS
Documentation <http://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_CreateStack.html>`__.

parameters
~~~~~~~~~~

.. DANGER::

    Sensitive data such as passwords or secret keys should not be stored in
    plaintext in stack config files. Instead, they should be passed in from
    the CLI with User Variables, or set via an environment variable with the
    environment variable resolver.

A dictionary of key-value pairs to be supplied to a template as
parameters. The keys must match up with the name of the parameter, and
the value must be of the type as defined in the template. Note that
Boto3 throws an exception if parameters are supplied to a template that
are not required by that template. Resolvers can be used to add
functionality to this key. Find out more in the  :ref:`Resolvers <Resolvers>` section.

A parameter can be specified either as a single value/resolver or a list
of values/resolvers. Lists of values/resolvers will be formatted into an
AWS compatible comma separated string e.g. ``value1,value2,value3``.
Lists can contain a mixture of values and resolvers.

Syntax:

.. code:: yaml

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

.. code:: yaml

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

protect
~~~~~~~

Stack protection against execution of the following commands:

-  ``launch-stack``
-  ``create-stack``
-  ``update-stack``
-  ``delete-stack``
-  ``execute-change-set``

If a user tries to run one of these commands on a protected stack,
Sceptre will throw an error.

sceptre\_user\_data
~~~~~~~~~~~~~~~~~~~

Represents data to be passed to the
``sceptre_handler(sceptre_user_data)`` function in Python templates or
accessible under ``sceptre_user_data`` variable key within Jinja2
templates.

stack\_name
~~~~~~~~~~~

A custom name name to use instead of the Sceptre default, e.g:

.. code:: yaml

    parameters:
        VpcID: !stack_output_external <custom-named-vpc-stack>::VpcID
    dependencies:
        - <environment>/<stack>

.. WARNING::

    Outputs from stacks with custom names can't be resolved using the
    standard stack output resolver. Outputs should be resolved using the
    stack output external resolver. An explicit dependency should be added,
    using the dependencies parameter, to make sure the stacks are launched
    in the correct order.

stack\_tags
~~~~~~~~~~~

A dictionary of `CloudFormation
Tags <https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_Tag.html>`__
to be applied to the stack.

role\_arn
~~~~~~~~~

The ARN of a `CloudFormation Service
Role <http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html>`__
that is assumed by CloudFormation to create, update or delete resources.

notifications
~~~~~~~~~~~~~

List of SNS topic ARNs to publish stack related events to. A maximum of
5 ARNs can be specified per stack. This configuration will be used by
the ``create-stack``, ``update-stack``, and ``create-change-set``
commands. More information about stack notifications can found under the
relevant section in the `AWS CloudFormation API
documentation <http://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_CreateStack.html>`__.

stack\_timeout
~~~~~~~~~~~~~~

A timeout in minutes before considering the stack deployment as failed.
After the specified timeout, the stack will be rolled back. Specifiyng
zero, as well as ommiting the field, will result in no timeout. Supports
only positive integer value.

template\_path
~~~~~~~~~~~~~~

The path to the CloudFormation, Jinja2 or Python template to build the
stack from. The path can either be absolute or relative to the Sceptre
Directory. Sceptre treats the template as CloudFormation, Jinja2 or
Python depending on the template's file extension. Note that the
template filename may be different from the stack config filename.

Cascading Config
----------------

Stack config can be cascaded in the same way Environment config can be,
as described in the section in Environment Config on `Cascading
Config <%7B%7B%20site.baseurl%20%7D%7D/docs/environment_config.html#cascading-config>`__.

.. WARNING::

    Cascading stack config is being deprecated, and should not be used.


Templating
----------

Stack config supports templating in the same way Environment config can
be, as described in the section in Environment Config on
`Templating <%7B%7B%20site.baseurl%20%7D%7D/docs/environment_config.html#templating>`__.

Stack config makes environment config available to template.

Environment config
~~~~~~~~~~~~~~~~~~

Environment config properties are available via the environment\_config
variable when using templating.

.. code:: yaml

    parameters:
      Region: {{ environment_config.region }}

Environment Variables
---------------------

It is possible to replace values in stack config files with environment
variables in two ways. For an explanation on why this is the case, see
the
`FAQ <%7B%7B%20site.baseurl%20%7D%7D/docs/faq.html#why-are-there-two-ways-to-supply-environment-variables-in-stack-config-files>`__.

Sceptre User Data
-----------------

Python or Jinja templates can contain data which should be
parameterised, but can't be parameterised using CloudFormation
parameters. An example of this is if a Python template which creates an
IAM Role reads in the policy from a JSON file. The file path must be
hardcoded in the Python template.

Sceptre user data allows users to store arbitrary key-value pairs in
their ``<stack-name>.yaml`` file. This data is then passed as a Python
``dict`` to the ``sceptre_handler(sceptre_user_data)`` function in
Python templates.

Syntax:

.. code:: yaml

    sceptre_user_data:
        iam_policy_file_path: /path/to/policy.json

When compiled, ``sceptre_user_data`` would be the dictionary
``{"iam_policy_file": "/path/to/policy.json"}``.

Examples
--------

.. code:: yaml

    template_path: templates/example.py
    parameters:
        param_1: value_1
        param_2: value_2

.. code:: yaml

    template_path: templates/example.json
    dependencies:
        - vpc
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
