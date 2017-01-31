.. highlight:: shell

=================
Advanced Patterns
=================

This section details patterns and techniques that advanced users may want to use.


.. _using_an_environments_connection_manager:

Using an Environment's Connection Manager
-----------------------------------------

When using Sceptre as a Python module, it is possible to make use of an environment's connection manager to make Boto3 calls to that environment's account and region, using the credentials set in environment config.

Once an environment is initialised, the connection manager can be accessed as follows:

.. code-block:: python

  from sceptre.environment import Environment

  env = Environment(
    sceptre_dir="string",
    environment_path="string",
    options={}
  )

  client = env.connection_manager._get_client("<service name>")

Where <service name> can be any of the services `supported by Boto3 <http://boto3.readthedocs.io/en/latest/reference/services/index.html>`_.

This client is a normal Boto3 client, and can be used as such.

.. _user_defined_resolvers:

Custom Resolvers
----------------------

Users can define their own resolvers which are used by Sceptre to resolve the value of a parameter before it is passed to the CloudFormation template.

A resolver is a Python class which inherits from abstract base class ``Resolver`` found in the ``sceptre.resolvers module``.

Resolvers are require to implement a ``resolve()`` function that takes no parameters and to call the base class initializer on initialisation.

Resolvers may have access to ``argument``,  ``stack_config``, ``environment_config`` and ``connection_manager`` as an attribute of ``self``. For example ``self.stack_config``.

This class should be defined in a file which is located at::

  <sceptre_project_dir>/resolvers/<your resolver>.py

An arbitrary file name may be used as it is not checked by Sceptre.

The following python module template can be copied and used:

.. code-block:: python

  from sceptre.resolvers import Resolver

  class CustomResolver(Resolver):

      def __init__(self, *args, **kwargs):
        super(EnvironmentVariable, self).__init__(*args, **kwargs)

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


This resolver can be used in a stack config file with the following syntax::

  template_path: <...>
  parameters:
    param1:
      <your resolver name>: <value>  # <your resolver name>
                                     # should match Hook.name.
                                     # <value> will be passed to the
                                     # resolver's resolve() method.


.. _user_defined_sceptre_hooks:

Custom Hooks
------------------

Users can define their own custom hooks, allowing users to extend hooks and integrate additional functionality into Sceptre projects.

A hook is a Python class which inherits from abstract base class ``Hook`` found in the ``sceptre.hooks module``.

Hooks are require to implement a ``run()`` function that takes no parameters and to call the base class initializer on initialisation.

Hooks may have access to ``argument``,  ``stack_config``, ``environment_config`` and ``connection_manager`` as an attribute of ``self``. For example ``self.stack_config``.

Hook classes are defined in python files located at::

  <sceptre_project_dir>/hooks/<your hook>.py

Sceptre retrieves any class which inherits from base class Hook found within this directory. The name of the hook is the class name in snake case format. e.g. ``class CustomHook`` is ``custom_hook``.  An arbitrary file name may be used as it is not checked by Sceptre.

The following python module template can be copied and used:

.. code-block:: python

  from sceptre.hooks import Hook


  class CustomHook(Hook):

      def __init__(self, *args, **kwargs):
          super(CustomHook, self).__init__(*args, **kwargs)

      def run(self):
          """
          run is the method called by Sceptre. It should carry out the work
          intended by this hook.

          self.argument is available from the base class and contains the
          argument defined in the sceptre config file (see below)

          The following attributes may be available from the base class:
          self.stack_config  (A dict of data from <stack_name>.yaml)
          self.environment_config  (A dict of data from config.yaml)
          self.connection_manager (A connection_manager)
          """
          print self.argument


This hook can be used in a stack config file with the following syntax::

  template_path: <...>
  before_create:
    - !custom_hook <argument>  # The argument is accessible via self.argument

.. _configuring_an_iam_role_for_sceptre:

Configuring an IAM role for Sceptre
-----------------------------------

When Sceptre is used in a situation requiring cross-account access or federation it is possible for it to assume a role before doing anything. This pattern demonstrates how one can use Sceptre itself to perform the initial setup of this role.

We build on previous sections (specifically :ref:`installation`, :doc:`get_started`, :doc:`command_line`, :doc:`environment_config`, :doc:`stack_config`, :doc:`templates`) so it is recommended you read and understand these sections before following this example.

First make sure you are working in the ``account-setup`` directory of the ``sceptre-tools`` repository.::

  $ git clone git@bitbucket.org:cloudreach/sceptre-tools.git
  $ cd sceptre-tools/account-setup

And ensure your Python environment contains the Troposphere template requirements.::

  $ pip install -U -r requirements.txt

Check Sceptre environment configuration in ``config/config.yaml`` (if desired you can hard-code configuration items rather specifying on the command line)

.. code-block:: yaml

  project_code: "{{ var.my_org | default('example') }}"
  region: "us-east-1"
  template_bucket_name: "{{ var.my_org | default('example') }}-sceptre"

Likewise check CloudFormation stack configuration in ``config/sceptre-iam-role.yaml``

.. code-block:: yaml

  template_path: templates/sceptre-iam-role.py
  sceptre_user_data:
    trusted_entity: "arn:aws:iam::{{ var.account_id | default('123456789012') }}:root"
    bucket_prefix: "{{ var.my_org | default('example') }}-sceptre"

You can of course also inspect or modify the Troposphere template in ``templates/sceptre-iam-role.py``

Use Sceptre to launch the CloudFormation stack with the desired variable substitutions::

  sceptre --var "my_org=YOUR-ORG" --var "account_id=TRUSTED-ACCOUNT-ID" launch-stack "" sceptre-iam-role

Finally you can pull the output of the CloudFormation stack into your local shell environment::

  $ eval $(sceptre describe-stack-outputs "" sceptre-iam-role --export=envvar)

And start using ``iam_role`` referencing shell environment variable in your Sceptre environment ``config.yaml``. For example item values will be replaced with environment variables:

.. code-block:: yaml

  iam_role: {{ environment_variable.SCEPTRE_RoleARN }}
  region: eu-west-1
  project_code: prj
  template_bucket_name: sceptre-artifacts

Where ``SCEPTRE_RoleARN`` is the name of exported environment variable.
