Resolvers
=========

Sceptre implements resolvers, which can be used to resolve a value of a
CloudFormation ``parameter`` or ``sceptre_user_data`` value at runtime. This is
most commonly used to chain the outputs of one Stack to the inputs of another.

If required, users can create their own resolvers, as described in the section
on `Custom Resolvers`_.

Syntax:

.. code-block:: yaml

   parameters:
     <parameter_name>: !<resolver_name> <resolver_value>
   sceptre_user_data:
     <name>: !<resolver_name> <resolver_value>

Available Resolvers
-------------------

environment_variable
~~~~~~~~~~~~~~~~~~~~

Fetches the value from an environment variable.

Syntax:

.. code-block:: yaml

   parameter|sceptre_user_data:
     <name>: !environment_variable ENVIRONMENT_VARIABLE_NAME

Example:

.. code-block:: yaml

   parameters:
       database_password: !environment_variable DATABASE_PASSWORD

file
~~~~

A Sceptre resolver to get file contents. The returned value can be passed into a parameter as
a string, json, or yaml object.

Refer to `sceptre-file-resolver <https://github.com/Sceptre/sceptre-file-resolver/>`_ for documentation.

file_contents
~~~~~~~~~~~~~

**deprecated**: Consider using the `file`_ resolver instead.

no_value
~~~~~~~~

This resolver "resolves to nothing", functioning just as if it was not set at all. This works just
like the "AWS::NoValue" special variable that you can reference on a CloudFormation template. It
can help simplify Stack and StackGroup config Jinja logic in cases where, if a condition is met, a
value is passed, otherwise no value is passed.

rcmd
~~~~

A resolver to execute any shell command.

Refer to `sceptre-resolver-cmd <https://github.com/Sceptre/sceptre-resolver-cmd/>`_ for documentation.

stack_output
~~~~~~~~~~~~

Fetches the value of an output from a different Stack controlled by Sceptre.

Syntax:

.. code-block:: yaml

   parameters | sceptre_user_data:
     <name>: !stack_output <stack_name>.yaml::<output_name>

Example:

.. code-block:: yaml

   parameters:
       VpcIdParameter: !stack_output shared/vpc.yaml::VpcIdOutput

Sceptre infers that the Stack to fetch the output value from is a dependency,
and builds that Stack before the current one.

This resolver will add a dependency for the Stack in which needs the output
from.

stack_output_external
~~~~~~~~~~~~~~~~~~~~~

Fetches the value of an output from a different Stack in the same account and
region. You can specify a optional AWS profile to connect to a different
account/region.

If the Stack whose output is being fetched is in the same StackGroup, the
basename of that Stack can be used.

Syntax:

.. code-block:: yaml

   parameters/sceptre_user_data:
     <name>: !stack_output_external <full_stack_name>::<output_name> <optional-aws-profile-name>

Example:

.. code-block:: yaml

   parameters:
     VpcIdParameter: !stack_output_external prj-network-vpc::VpcIdOutput prod

Custom Resolvers
----------------

Users can define their own resolvers which are used by Sceptre to resolve the
value of a parameter before it is passed to the CloudFormation template.

A resolver is a Python class which inherits from abstract base class
``Resolver`` found in the ``sceptre.resolvers module``.

Resolvers are require to implement a ``resolve()`` function that takes no
parameters and to call the base class initializer on initialisation.

Resolvers may have access to ``argument``, ``stack_config``,
``stack_group_config`` and ``connection_manager`` as an attribute of ``self``.
For example ``self.stack_config``.

Sceptre uses the ``sceptre.resolvers`` entry point to locate resolver classes.
Your custom resolver can be written anywhere and is installed as Python
package.
In case you are not familiar with python packaging, `this is great place to start`_.

Example
~~~~~~~

The following python module template can be copied and used:

.. code-block:: text

   custom_resolver
   ├── custom_resolver.py
   └── setup.py

The following python module template can be copied and used:

custom_resolver.py
^^^^^^^^^^^^^^^^^^

.. code-block:: python

        from sceptre.resolvers import Resolver


        class CustomResolver(Resolver):
            """
            The following instance attributes are inherited from the parent class Resolver.

            Parameters
            ----------
            argument: Any
                The argument of the resolver. This can be any value able to be defined in yaml.
            stack: sceptre.stack.Stack
                The associated stack of the resolver. This will normally be None when the resolver is
                instantiated, but will be set before the resolver is resolved.
            """

            def __init__(self, argument, stack=None):
                super(CustomResolver, self).__init__(argument, stack)

            def setup(self):
                """
                Setup is invoked after the stack has been set on the resolver, whether or not the
                resolver is ever resolved.

                Implement this method for any setup behavior you want (such as adding to stack dependencies).
                """

            def resolve(self):
                """
                resolve is the method called by Sceptre. It should carry out the work
                intended by this resolver. It should return a string to become the
                final value.

                To use instance attribute self.<attribute_name>.

                Examples
                --------
                self.argument
                self.stack

                Returns
                -------
                str
                    Resolved value
                """
                return self.argument


setup.py
^^^^^^^^

.. code-block:: python

   from setuptools import setup

   setup(
       name='<custom_resolver_package_name>',
       py_modules=['<custom_resolver_module_name>'],
       entry_points={
           'sceptre.resolvers': [
               '<custom_resolver_command_name> = <custom_resolver_module_namef>:CustomResolver',
           ],
       }
   )

Then install using ``python setup.py install`` or ``pip install .`` commands.

This resolver can be used in a Stack config file with the following syntax:

.. code-block:: yaml

   template:
     path: <...>
     type: <...>
   parameters:
     param1: !<custom_resolver_command_name> <value> <optional-aws-profile>


Resolver arguments
^^^^^^^^^^^^^^^^^^
Resolver arguments can be a simple string or a complex data structure.

.. code-block:: yaml

   template:
     path: <...>
     type: <...>
    parameters:
      Param1: !ssm "/dev/DbPassword"
      Param2: !ssm {"name": "/dev/DbPassword"}
      Param3: !ssm
        name: "/dev/DbPassword"

.. _Custom Resolvers: #custom-resolvers
.. _this is great place to start: https://docs.python.org/3/distributing/

Resolving to nothing
^^^^^^^^^^^^^^^^^^^^
When a resolver returns ``None``, this means that it resolves to "nothing". For resolvers set for
single values (such as for ``template_bucket_name`` or ``role_arn``), this just means the value is
``None`` and treated like those values aren't actually set. But for resolvers inside of containers
like lists or dicts, when they resolve to "nothing", that item gets completely removed from their
containing list or dict.

This feature would be useful if you wanted to define a resolver that sometimes would resolve to be a
given stack parameter and sometimes would be not defined at all and use the template's default value
for that parameter. The resolver could just return `None` in those cases it wants to resolve to
nothing, similar to the AWS::NoValue pseudo-parameter that can be referenced in a CloudFormation
template.

Resolver placeholders
^^^^^^^^^^^^^^^^^^^^^
Resolvers (especially the !stack_output resolver) often express dependencies on other stacks and
their outputs. However, there are times when those stacks or outputs will not exist yet because they
have not yet been deployed. During normal deployment operations (using the ``launch``, ``create``,
``update``, and ``delete`` commands), Sceptre knows the correct order to resolve dependencies in and will
ensure that order is followed, so everything works as expected.

But there are other commands that will not actually deploy dependencies of a stack config before
operating on that Stack Config. These commands include ``generate``, ``validate``, and ``diff``.
If you have used resolvers to reverence other stacks, it is possible that a resolver might not be able
to be resolved when performing that command's operations and will trigger an error. This is not likely
to happen when you have only used resolvers in a stack's ``parameters``, but it is much more likely
if you have used them in ``sceptre_user_data`` with a Jinja or Python template. At those times (and
only when a resolver cannot be resolved), a **best-attempt placeholder value** will be supplied in to
allow the command to proceed. Depending on how your template or Stack Config is configured, the
command may or may not actually succeed using that placeholder value.

A few examples...

* If you have a stack parameter referencing ``!stack_output other_stack.yaml::OutputName``,
  and you run the ``diff`` command before other_stack.yaml has been deployed, the diff output will
  show the value of that parameter to be ``"{ !StackOutput(other_stack.yaml::OutputName) }"``.
* If you have a ``sceptre_user_data`` value used in a Jinja template referencing
  ``!stack_output other_stack.yaml::OutputName`` and you run the ``generate`` command, the generated
  template will replace that value with ``"StackOutputotherstackyamlOutputName"``. This isn't as
  "pretty" as the sort of placeholder used for stack parameters, but the use of sceptre_user_data is
  broader, so it placeholder values can only be alphanumeric to reduce chances of it breaking the
  template.
* Resolvable properties that are *always* used when performing template operations (like ``iam_role``
  and ``template_bucket_name``) will resolve to ``None`` and not be used for those operations if they
  cannot be resolved.

Any command that allows these placeholders can have them disabled with the ``--no-placeholders`` ClI
option.
