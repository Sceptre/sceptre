StackGroup Config
=================

StackGroup config stores information related to the StackGroup, such as a
particular profile to use, the name of the S3 bucket in which to store
templates, and the target region in which to build resources. StackGroup config
is stored in various files around the directory structure, all with the name
``config.yaml``.

Structure
---------

An StackGroup config file is a yaml object of key-value pairs configuring
Sceptre. The available keys are listed below.

-  `project_code`_ *(required)*
-  `region`_ *(required)*
-  `profile`_ *optional*
-  `required_version`_ *(optional)*
-  `template_bucket_name`_ *(optional)*
-  `template_key_prefix`_ *(optional)*
-  `j2_environment`_ *(optional)*
-  `http_template_handler`_ *(optional)*

Sceptre will only check for and uses the above keys in StackGroup config files
and are directly accessible from Stack(). Any other keys added by the user are
made available via ``stack_group_config`` attribute on ``Stack()``.

profile
~~~~~~~
* Resolvable: No
* Inheritance strategy: Overrides parent if set by child

The name of the profile as defined in ``~/.aws/config`` and ``~/.aws/credentials``. Use the
`aws configure --profile <profile_id>` command form the AWS CLI to add profiles to these files.

For more information on this configuration, its implications, and its uses, see
:ref:`Sceptre and IAM: profile <profile_permissions>`.

Reference: `AWS_CLI_Configure`_

project_code
~~~~~~~~~~~~
* Resolvable: No
* Inheritance strategy: Overrides parent if set by child

A string which is prepended to the Stack names of all Stacks built by Sceptre.

region
~~~~~~
* Resolvable: No
* Inheritance strategy: Overrides parent if set by child

The AWS region to build Stacks in. Sceptre should work in any `region which
supports CloudFormation`_.

template_bucket_name
~~~~~~~~~~~~~~~~~~~~
* Resolvable: Yes
* Inheritance strategy: Overrides parent if set by child

The name of an S3 bucket to upload CloudFormation Templates to. Note that S3
bucket names must be globally unique. If the bucket does not exist, Sceptre
creates one using the given name, in the AWS region specified by ``region``.

If this parameter is not added, Sceptre does not upload the template to S3, but
supplies the template to Boto3 via the ``TemplateBody`` argument. Templates
supplied in this way have a lower maximum length, so using the
``template_bucket_name`` parameter is recommended.

.. warning::

   If you resolve ``template_bucket_name`` using the ``!stack_output``
   resolver on a StackGroup, the stack that outputs that bucket name *cannot* be
   defined in that StackGroup. Otherwise, a circular dependency will exist and Sceptre
   will raise an error when attempting any Stack action. There are two ways to avoid this situation:

   1. Set the ``template_bucket_name`` to ``!no_value`` in on the StackConfig that creates your
      template bucket. This will override the inherited value to prevent them from having
      dependencies on themselves.
   2. Define all your project stacks inside a StackGroup and then your template bucket
      stack *outside* that StackGroup. Here's an example project structure for something like
      this:

      .. code-block:: yaml

         config/
           - config.yaml           # This is the StackGroup Config for your whole project.
           - template-bucket.yaml  # The template for this stack outputs the bucket name
           - project/              # You can put all your other stacks in this StackGroup
               - config.yaml       # In this StackGroup Config is...
                                   #  template_bucket_name: !stack_output template-bucket.yaml::BucketName
               - vpc.yaml          # Put all your other project stacks inside project/
               - other-stack.yaml


template_key_prefix
~~~~~~~~~~~~~~~~~~~
* Resolvable: No
* Inheritance strategy: Overrides parent if set by child

A string which is prefixed onto the key used to store templates uploaded to S3.
Templates are stored using the key:

.. code-block:: text

   <template_key_prefix>/<region>/<stack_group>/<stack_name>-<timestamp>.<extension>

Template key prefix can contain slashes (“/”), which are displayed as
directories in the S3 console.

Extension can be ``json`` or ``yaml``.

Note that if ``template_bucket_name`` is not supplied, this parameter is
ignored.

j2_environment
~~~~~~~~~~~~~~
* Resolvable: No
* Inheritance strategy: Child configs will be merged with parent configs

A dictionary that is combined with the default jinja2 environment.
It's converted to keyword arguments then passed to [jinja2.Environment](https://jinja.palletsprojects.com/en/2.11.x/api/#jinja2.Environment).
This will impact the templating of stacks by modifying the behavior of jinja.

.. code-block:: yaml

   j2_environment:
      extensions:
         - jinja2.ext.i18n
         - jinja2.ext.do
      lstrip_blocks: True
      trim_blocks: True
      newline_sequence: \n

http_template_handler
~~~~~~~~~~~~~~~~~~~~~

Options passed to the `http template handler`_.
  * retries - The number of retry attempts (default is 5)
  * timeout - The timeout for the session in seconds (default is 5)

.. code-block:: yaml

   http_template_handler:
      retries: 10
      timeout: 20

require_version
~~~~~~~~~~~~~~~

A `PEP 440`_ compatible version specifier. If the Sceptre version does not fall
within the given version requirement it will abort.

.. _stack_group_config_cascading_config:

Cascading Config
----------------

Using Sceptre, config files are cascaded. Given the following sceptre directory
structure:

.. code-block:: text

   .
   └── config
       ├── account-1
       │   ├── config.yaml
       │   └── dev
       │       └── config.yaml
       └── config.yaml

General configurations should be defined at a high level, and more specific
configurations should be defined at a lower directory level.

YAML files that define configuration settings with conflicting keys, the child
configuration file will usually take precedence (see the specific config keys as documented
for the inheritance strategy employed).

In the above directory structure, ``config/config.yaml`` will be read in first,
followed by ``config/account-1/config.yaml``, followed by
``config/account-1/dev/config.yaml``.

For example, if you wanted the ``dev`` StackGroup to build to a different
region, this setting could be specified in the ``config/dev/config.yaml`` file,
and would only be applied to builds in the ``dev`` StackGroup.

.. _setting_dependencies_for_stack_groups:

Setting Dependencies for StackGroups
------------------------------------
There are a few pieces of AWS infrastructure that Sceptre can (optionally) use to support the needs
and concerns of the project. These include:

* The S3 bucket where templates are uploaded to and then referenced from for stack actions (i.e. the
  ``template_bucket_name`` config key).
* The CloudFormation service role added to the stack(s) that CloudFormation uses to execute stack
  actions (i.e. the ``role_arn`` config key).
* The role that Sceptre will assume to execute stack actions (i.e. the ``iam_role`` config key).
* SNS topics that cloudformation will notify with the results of stack actions (i.e. the
  ``notifications`` config key).

These sorts of dependencies CAN be defined in Sceptre and added at the StackGroup level, referenced
using ``!stack_output``. Doing so will make it so that every stack in the StackGroup will have those
dependencies and get those values from Sceptre-managed stacks.

Beyond the above mentioned config keys, it is possible to set the ``dependencies`` config key in a
StackGroup config to be inherited by all Stack configs in that group. All dependencies in child
stacks will be added to their inherited StackGroup dependencies, so be careful how you structure
dependencies.

.. warning::

   You might have already considered that this might cause a circular dependency for those
   dependency stacks, the ones that output the template bucket name, role arn, iam_role, or topic arns.
   In order to avoid the circular dependency issue, you can either:

   1. Set the value of those configurations to ``!no_value`` in the actual stacks that define those
      items so they don't inherit a dependency on themselves.
   2. Define those stacks *outside* the StackGroup you reference them in. Here's an example project
      structure that would support doing this:

      .. code-block:: yaml

        config/
          - config.yaml               # This is the StackGroup Config for your whole project.
          - sceptre-dependencies.yaml # This stack defines your template bucket, iam role, topics, etc...
          - project/                  # You can put all your other stacks in this StackGroup
              - config.yaml           # In this StackGroup Config you can use !stack_output to
                                      # reference outputs from sceptre-dependencies.yaml.
              - vpc.yaml              # Put all your other project stacks inside project/
              - other-stack.yaml


.. _stack_group_config_templating:

Templating
----------

Sceptre supports the use of templating in config files. Templating allows
config files to be further configured using values from the command line,
environment variables, files or parts of the ``command_path``.

Internally, Sceptre uses Jinja2 for templating, so any valid Jinja2 syntax
should work with Sceptre templating.

Templating can be used for any values in the config files, not just those that
are used by Sceptre.

Var
~~~

User variables are used to replace the value of any item in a config file with
a value defined by a CLI flag or in a YAML variable file:

.. code-block:: yaml

   profile: {{ var.profile }}
   region: eu-west-1

This item can be set using either a command line flag:

.. code-block:: text

   sceptre --var "profile=<your profile>" <COMMAND>

Or from a YAML variable file:

.. code-block:: text

   sceptre --var-file=variables.yaml <COMMAND>

where ``variables.yaml`` contains:

.. code-block:: yaml

   profile: <your profile>

Both the ``--var`` and ``--var-file`` flags can be used multiple times. If
multiple ``--var-file`` options are supplied, the variables from these files
will be merged, with a higher precedence given to options specified later in
the command. Values supplied using ``--var`` take the highest precedence and
will overwrite any value defined in the variable files.

For example if we have the following variable files:

.. code-block:: yaml

   # default.yaml
   region: eu-west-1
   profile: dev
   project_code: api

.. code-block:: yaml

   # prod.yaml
   profile: prod

The following sceptre command:

.. code-block:: text

   sceptre --var-file=default.yaml --var-file=prod.yaml --var region=us-east-1 <COMMAND>

Will result in the following variables being available to the jinja templating:

.. code-block:: yaml

   region: us-east-1
   profile: prod
   project_code: api

Note that by default, dictionaries are not merged. If the variable appearing in
the last variable file is a dictionary, and the same variable is defined in an
earlier variable file, that whole dictionary will be overwritten. For example,
this would not work as intended:

.. code-block:: yaml

   # default.yaml
   tags: {"Env": "dev", "Project": "Widget"}

.. code-block:: yaml

   # prod.yaml
   tags: {"Env": "prod"}

Rather, the final dictionary would only contain the ``Env`` key.

By using the ``--merge-vars`` option, these tags can be merged as intended:

.. code-block:: text

    sceptre --merge-vars --var-file=default.yaml --var-file=prod.yaml --var region=us-east-1 <COMMAND>

This will result in the following:

.. code-block:: yaml

    tags: {"Env": "prod", "Project": "Widget"}

For command line flags, Sceptre splits the string on the first equals sign “=”,
and sets the key to be the first substring, and the value to be the second. Due
to the large number of possible user inputs, no error checking is performed on
the value of the –var flag, and it is the user’s responsibility to make sure
that the value is correctly formatted.

All user variables are supplied to all config files, so users must be careful
to make sure that user variable names do not unintentionally clash.

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Config item values can be replaced with environment variables:

.. code-block:: yaml

   profile: {{ environment_variable.PROFILE }}
   region: eu-west-1

Where ``PROFILE`` is the name of an environment variable.

Command Path
~~~~~~~~~~~~

Config item values can be replaced with parts of the ``command_path``

.. code-block:: yaml

   region: {{ command_path.0 }}
   profile: default

Where the value is taken from the first part of the ``command_path`` from the
invoking sceptre command:

.. code-block:: text

   sceptre launch eu-west-1/dev/vpc.yaml

Template Defaults
~~~~~~~~~~~~~~~~~

Any templated value can be supplied with a default value with the syntax:

.. code-block:: text

   {{ var.value | default("default_value") }}

Examples
--------

.. code-block:: yaml

   profile: profile
   project_code: prj
   region: eu-west-1
   template_bucket_name: sceptre-artifacts
   template_key_prefix: my/prefix

.. code-block:: yaml

   profile: {{ var.profile }}
   project_code: {{ var.project_code | default("prj") }}
   region: {{ command_path.2 }}
   template_bucket_name: {{ environment_variable.TEMPLATE_BUCKET_NAME }}

.. _project_code: #project_code
.. _region: #region
.. _profile: #profile
.. _required_version: #required_version
.. _template_bucket_name: #template_bucket_name
.. _template_key_prefix: #template_key_prefix
.. _region which supports CloudFormation: http://docs.aws.amazon.com/general/latest/gr/rande.html#cfn_region
.. _PEP 440: https://www.python.org/dev/peps/pep-0440/#version-specifiers
.. _AWS_CLI_Configure: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html
.. _http template handler: template_handlers.html#http
