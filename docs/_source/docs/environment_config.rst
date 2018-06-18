Environment Config
==================

Environment config stores information related to the environment, such
as a particular IAM role to assume, the name of the S3 bucket in which
to store templates, and the target region in which to build resources.
Environment config is stored in various files around the directory
structure, all with the name ``config.yaml``.

Structure
---------

An environment config file is a yaml object of key-value pairs
configuring Sceptre. The available keys are listed below.

-  `iam\_role`_ *(optional)*
-  `profile`_ *optional*
-  `project\_code`_ *(required)*
-  `region`_ *(required)*
-  `template\_bucket\_name`_ *(optional)*
-  `template\_key\_prefix`_ *(optional)*
-  `require\_version`_ *(optional)*

Sceptre only checks for and uses the above keys in environment config
files, but any others added by the user are read in and are made
available to the user via the
``sceptre.environment.Environment().config`` attribute.

iam\_role
~~~~~~~~~

The ARN of a role for Sceptre to assume before interacting with the
environment. If not supplied, Sceptre uses the user's AWS CLI
credentials.

profile
~~~~~~~

The name of the profile as defined in ~/.aws/config and
~/.aws/credentials. If ``iam_role`` is also provided, Sceptre will use
``profile`` to assume the ``iam_role``. If ``iam_role`` is not provided,
Sceptre will use ``profile`` to interact with the environment.

project\_code
~~~~~~~~~~~~~

A code which is prepended to the stack names of all stacks built by
Sceptre.

region
~~~~~~

The AWS region to build stacks in. Sceptre should work in any `region
which supports
CloudFormation <http://docs.aws.amazon.com/general/latest/gr/rande.html#cfn_region>`__.

template\_bucket\_name
~~~~~~~~~~~~~~~~~~~~~~

The name of an S3 bucket to upload CloudFormation Templates to. Note
that S3 bucket names must be globally unique. If the bucket does not
exist, Sceptre creates one using the given name, in the AWS region
specified by ``region``.

If this parameter is not added, Sceptre does not upload the template to
S3, but supplies the template to Boto3 via the ``TemplateBody``
argument. Templates supplied in this way have a lower maximum length, so
using the ``template_bucket_name`` parameter is recommended.

template\_key\_prefix
~~~~~~~~~~~~~~~~~~~~~

A string which is prefixed onto the key used to store templates uploaded
to S3. Templates are stored using the key:

::

    <template_key_prefix>/<region>/<environment>/<stack_name>-<timestamp>.<extension>

Template key prefix can contain slashes ("/"), which are displayed as
directories in the S3 console.

Extension can be ``json`` or ``yaml``.

Note that if ``template_bucket_name`` is not supplied, this parameter is
ignored.

require\_version
~~~~~~~~~~~~~~~~

A `PEP
440 <https://www.python.org/dev/peps/pep-0440/#version-specifiers>`__
compatible version specifier. If the Sceptre version does not fall
within the given version requirement it will abort.

Cascading Config
----------------

Using Sceptre, config files can be cascaded. Given the following sceptre
directory structure:

::

    .
    └── config
        ├── account-1
        │   ├── config.yaml
        │   └── dev
        │       └── config.yaml
        └── config.yaml

General configurations should be defined at a high level, and more
specific configurations should be defined at a lower directory level.
YAML files which define configuration settings with names which overlap
will take precedence if they are deeper in the directory structure. For
example, if you wanted the dev environment to build to a different
region, this setting could be specified in the config/dev/config.yaml
file, and would only be applied to builds in the dev environment.

In the above directory structure, ``config/config.yaml`` will be read in
first, followed by ``config/account-1/config.yaml``, followed by
``config/account-1/dev/config.yaml``. Config files read in later
overwrite any key-value pairs shared by those previously read in. Thus
general config can be defined at a high level, and more specific config
can be defined at a lower directory level.

.. _Templating:

Templating
----------

Sceptre supports the use of templating in config files. Templating
allows config files to be further configured using values from the
command line, environment variables, files or parts of the environment
path.

Internally, Sceptre uses Jinja2 for templating, so any valid Jinja2
syntax should work with Sceptre templating.

Templating can be used for any values in the config files, not just
those that are used by Sceptre.

Var
~~~

User variables are used to replace the value of any item in a config
file with a value defined by a cli flag or in a YAML variable file:

.. code:: yaml

    iam_role: {{ var.iam_role }}
    region: eu-west-1

This item can be set using either a command line flag:

.. code:: shell

    $ sceptre --var "iam_role=<your iam role>" <COMMAND>

Or from a YAML variable file:

.. code:: shell

    $ sceptre --var-file=variables.yaml <COMMAND>

where ``variables.yaml`` contains::

.. code:: yaml

    iam_role: <your iam role>

Both the ``--var`` and ``--var-file`` flags can be used multiple times.
If multiple ``--var-file`` options are supplied, the variables from
these files will be merged, with a higher precedence given to options
specified later in the command. Values supplied using ``--var`` take the
highest precedence and will overwrite any value defined in the variable
files.

For example if we have the following variable files:

.. code:: yaml

    ---- default.yaml
    region: eu-west-1
    profile: dev
    project_code: api

    ---- prod.yaml
    profile: prod

The following sceptre command:

.. code:: shell

    sceptre --var-file=default.yaml --var-file=prod.yaml --var region=us-east-1 <COMMAND>

Will result in the following variables being available to the jinja
templating:

.. code:: yaml

    region: us-east-1
    profile: prod
    project_code: api

For command line flags, Sceptre splits the string on the first equals
sign "=", and sets the key to be the first substring, and the value to
be the second. Due to the large number of possible user inputs, no error
checking is performed on the value of the --var flag, and it is the
user's responsibility to make sure that the value is correctly
formatted.

All user variables are supplied to all config files, so users must be
careful to make sure that user variable names do not unintentionally
clash.

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Config item values can be replaced with environment variables:

.. code:: yaml

    iam_role: {{ environment_variable.IAM_ROLE }}
    region: eu-west-1

Where ``IAM_ROLE`` is the name of an environment variable.

Environment Path
~~~~~~~~~~~~~~~~

Config item values can be replaced with parts of the environment path:

.. code:: yaml

    region: {{ environment_path.0 }}
    iam_role: role

Where the value is taken from the first part of the environment path
from the invoking sceptre command:

.. code:: shell

    $ sceptre launch-stack eu-west-1/dev vpc

Template Defaults
~~~~~~~~~~~~~~~~~

Any templated value can be supplied with a default value with the
syntax:

.. code:: yaml

    {{ var.value | default("default_value") }}

Examples
--------

.. code:: yaml

    iam_role: arn:aws:iam::123456789012:role/sceptrerole
    project_code: prj
    region: eu-west-1
    template_bucket_name: sceptre-artifacts
    template_key_prefix: my/prefix

.. code:: yaml

    iam_role: {{ var.iam_role }}
    project_code: {{ var.project_code | default("prj") }}
    region: {{ environment_path.2 }}
    template_bucket_name: {{ environment_variable.TEMPLATE_BUCKET_NAME }}
