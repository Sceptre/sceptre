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

Sceptre will only check for and uses the above keys in StackGroup config files
and are directly accessible from Stack(). Any other keys added by the user are
made available via ``stack_group_confg`` attribute on ``Stack()``.

profile
~~~~~~~

The name of the profile as defined in ``~/.aws/config`` and
``~/.aws/credentials``.

project_code
~~~~~~~~~~~~

A string which is prepended to the Stack names of all Stacks built by Sceptre.

region
~~~~~~

The AWS region to build Stacks in. Sceptre should work in any `region which
supports CloudFormation`_.

template_bucket_name
~~~~~~~~~~~~~~~~~~~~

The name of an S3 bucket to upload CloudFormation Templates to. Note that S3
bucket names must be globally unique. If the bucket does not exist, Sceptre
creates one using the given name, in the AWS region specified by ``region``.

If this parameter is not added, Sceptre does not upload the template to S3, but
supplies the template to Boto3 via the ``TemplateBody`` argument. Templates
supplied in this way have a lower maximum length, so using the
``template_bucket_name`` parameter is recommended.

template_key_prefix
~~~~~~~~~~~~~~~~~~~

A string which is prefixed onto the key used to store templates uploaded to S3.
Templates are stored using the key:

.. code-block:: text

   <template_key_prefix>/<region>/<stack_group>/<stack_name>-<timestamp>.<extension>

Template key prefix can contain slashes (“/”), which are displayed as
directories in the S3 console.

Extension can be ``json`` or ``yaml``.

Note that if ``template_bucket_name`` is not supplied, this parameter is
ignored.

require_version
~~~~~~~~~~~~~~~

A `PEP 440`_ compatible version specifier. If the Sceptre version does not fall
within the given version requirement it will abort.


.. stack_group_config_cascading_config

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
configuration file will take precedence.

In the above directory structure, ``config/config.yaml`` will be read in first,
followed by ``config/account-1/config.yaml``, followed by
``config/account-1/dev/config.yaml``.

For example, if you wanted the ``dev`` StackGroup to build to a different
region, this setting could be specified in the ``config/dev/config.yaml`` file,
and would only be applied to builds in the ``dev`` StackGroup.

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

.. code-block:: jinja

   profile: {% raw %}{{ var.profile }}{% endraw %}
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

.. TODO split into 2 blocks

.. code-block:: yaml

   ---- default.yaml
   region: eu-west-1
   profile: dev
   project_code: api

   ---- prod.yaml
   profile: prod

The following sceptre command:

.. code-block:: text

   sceptre --var-file=default.yaml --var-file=prod.yaml --var region=us-east-1 <COMMAND>

Will result in the following variables being available to the jinja templating:

.. code-block:: yaml

   region: us-east-1
   profile: prod
   project_code: api

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

.. code-block:: jinja

   profile: {% raw %}{{ environment_variable.PROFILE }}{% endraw %}
   region: eu-west-1

Where ``PROFILE`` is the name of an environment variable.

Command Path
~~~~~~~~~~~~

Config item values can be replaced with parts of the ``command_path``

.. code-block:: jinja

   region: {% raw %}{{ command_path.0 }}{% endraw %}
   profile: default

Where the value is taken from the first part of the ``command_path`` from the
invoking sceptre command:

.. code-block:: text

   sceptre launch eu-west-1/dev/vpc.yaml

Template Defaults
~~~~~~~~~~~~~~~~~

Any templated value can be supplied with a default value with the syntax:

.. code-block:: jinja

   {% raw %}{{ var.value | default("default_value") }}{% endraw %}

Examples
--------

.. code-block:: yaml

   profile: profile
   project_code: prj
   region: eu-west-1
   template_bucket_name: sceptre-artifacts
   template_key_prefix: my/prefix

.. code-block:: jinja

   {% raw %}
   profile: {{ var.profile }}
   project_code: {{ var.project_code | default("prj") }}
   region: {{ command_path.2 }}
   template_bucket_name: {{ environment_variable.TEMPLATE_BUCKET_NAME }}
   {% endraw %}

.. _project_code: #project_code
.. _region: #region
.. _profile: #profile
.. _required_version: #required_version
.. _template_bucket_name: #template_bucket_name
.. _template_key_prefix: #template_key_prefix
.. _region which supports CloudFormation: http://docs.aws.amazon.com/general/latest/gr/rande.html#cfn_region
.. _PEP 440: https://www.python.org/dev/peps/pep-0440/#version-specifiers
