Resolvers
=========

Sceptre implements resolvers, which can be used to resolve a value of a
CloudFormation ``parameter`` or ``sceptre_user_data`` value at runtime. This is
most commonly used to chain the outputs of one Stack to the inputs of another.

You can use resolvers with any resolvable property on a StackConfig, as well as in the arguments
of hooks and other resolvers.

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

join
~~~~

This resolver allows you to join multiple strings together to form a single string. This is great
for combining the outputs of multiple resolvers. This resolver works just like CloudFormation's
``!Join`` intrinsic function.

The argument for this resolver should be a list with two elements: (1) A string to join the elements
on and (2) a list of items to join.

Example:

.. code-block:: yaml

   parameters:
     BaseUrl: !join
       - ":"
       - - !stack_output my/app/stack.yaml::HostName
         - !stack_output my/other/stack.yaml::Port


no_value
~~~~~~~~

This resolver "resolves to nothing", functioning just as if it was not set at all. This works just
like the "AWS::NoValue" special variable that you can reference on a CloudFormation template. It
can help simplify Stack and StackGroup config Jinja logic in cases where, if a condition is met, a
value is passed, otherwise no value is passed.

For example, you could use this resolver like this:

.. code-block:: yaml

   parameters:
    my_parameter: {{ var.some_value_that_might_not_be_set | default('!no_value') }}

In this example, if ``var.some_value_that_might_not_be_set`` is set, ``my_parameter`` will be set to
that value. But if ``var.some_value_that_might_not_be_set`` is not actually set, ``my_parameter``
won't even be passed to CloudFormation at all. This might be desired if there is a default value on
the CloudFormation template for ``my_parameter`` and we'd want to fall back to that default.

rcmd
~~~~

A resolver to execute any shell command.

Refer to `sceptre-resolver-cmd <https://github.com/Sceptre/sceptre-resolver-cmd/>`_ for documentation.

select
~~~~~~

This resolver allows you to select a specific index of a list of items. This is great for combining
with the ``!split`` resolver to obtain part of a string. This function works almost the same as
CloudFormation's ``!Select`` intrinsic function, **except you can use this with negative indices to
select from the end of a list**.

The argument for this resolver should be a list with two elements: (1) A numerical index and (2) a
list of items to select out of. If the index is negative, it will select from the end of the list.
For example, "-1" would select the last element and "-2" would select the second-to-last element.

Example:

.. code-block:: yaml

   sceptre_user_data:
     # This selects the last element after you split the connection string on "/"
     DatabaseName: !select
       - -1
       - !split ["/", !stack_output my/database/stack.yaml::ConnectionString]

split
~~~~~

This resolver will split a value on a given delimiter string. This is great when combining with the
``!select`` resolver. This function works the same as CloudFormation's ``!Split`` intrinsic function.

Note: The return value of this resolver is a *list*, not a string. This will not work to set Stack
configurations that expect strings, but it WILL work to set Stack configurations that expect lists.

The argument for this resolver should be a list with two elements: (1) The delimiter to split on and
(2) a string to split.

Example:

.. code-block:: yaml

   notifications: !split
     - ";"
     - !stack_output my/sns/topics.yaml::SemicolonDelimitedArns

.. _stack_attr_resolver:

stack_attr
~~~~~~~~~~

This resolver resolves to the values of other fields on the same Stack Config or those
inherited from StackGroups in which the current Stack Config exists, even when those other fields are
also resolvers.

To understand why this is useful, consider a stack's ``template_bucket_name``. This is usually set on
the highest level StackGroup Config. Normally, you could reference the template_bucket_name that was
set in an outer StackGroup Config with Jinja using ``{{template_bucket_name}}`` or, more explicitly, with
``{{stack_group_config.template_bucket_name}}``.

However, if the value of ``template_bucket_name`` is set with a resolver, using Jinja won't work.
This is due to the :ref:`resolution_order` on a Stack Config. Jinja configs are rendered *before*
resolvers are constructed or resolved, so you can't resolve a resolver from a StackGroup Config via
Jinja. That's where !stack_attr is useful. It's a resolver that resolves to the value of another stack
attribute (which could be another resolver).

.. code-block:: yaml

   template:
       type: sam
       path: path/from/my/cwd/template.yaml
       # template_bucket_name could be set by a resolver in the StackGroup.
       artifact_bucket_name: !stack_attr template_bucket_name

The argument to this resolver is the full attribute "path" from the Stack Config. You can access
nested values in dicts and lists using "." to separate key/index segments. For example:

.. code-block:: yaml

   sceptre_user_data:
       key:
           - "some random value"
           - "the value we want to select"

   sceptre_role: !stack_output roles.yaml::RoleArn

   parameters:
       # This will pass the value of "the value we want to select" for my_parameter
       my_parameter: !stack_attr sceptre_user_data.key.1
       # You can also access the value of another resolvable property like this:
       use_role: !stack_attr sceptre_role


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
adding that stack to the current stack's list of dependencies. This instructs
Sceptre to build that Stack before the current one.

.. warning::
   Be careful when using the stack_output resolver that you do not create circular dependencies.
   This is especially true when using this on StackGroup Configs to create configurations
   to be inherited by all stacks in that group. If the `!stack_output` resolver would be "inherited"
   from a StackGroup Config by the stack it references, this will lead to a circular dependency.
   The correct way to work around this is to move that stack outside that StackGroup so that it
   doesn't "inherit" that resolver.

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


sub
~~~

This resolver allows you to create a string using Python string format syntax. This functions as a
great way to combine together a number of resolver outputs into a single string. This functions
similarly to Cloudformation's ``!Sub`` intrinsic function.

It should be noted that Jinja2 syntax is far more capable of interpolating values than this resolver,
so you should use Jinja2 if all you need is to interpolate raw values from environment variables,
variables from stack group configs, var files, and ``--var`` arguments. **The one thing that Jinja2
interpolation can't do is interpolate resolver arguments into a string.** And that's what ``!sub``
can do. For more information on why Jinja2 can't reference resolvers directly, see
:ref:`resolution_order`.

The argument to this resolver should be a two-element list: (1) Is the format string, using
curly-brace templates to indicate variables, and (2) a dictionary where the keys are the format
string's variable names and the values are the variable values.

Example:

.. code-block:: yaml

   parameters:
     ConnectionString: !sub
       - "postgres://{username}:{password}@{hostname}:{port}/{database}"
       # Notice how we're interpolating a username and database via Jinja2? Technically it's not
       # necessary to pass them this way. They could be interpolated directly. But it might be
       # easier to read this way if you pass them explicitly like this. See example below for the
       # other way this can be done.
       - username: {{ var.username }}
         password: !ssm /my/ssm/password
         hostname: !stack_output my/database/stack.yaml::HostName
         port: !stack_output my/database/stack.yaml::Port
         database: {{var.database}}


It's relevant to note that this functions similarly to the *more verbose* form of CloudFormation's
``!Sub`` intrinsic function, where you use a list argument and supply the interpolated values as a
second list item in a dictionary. **Important**: Sceptre's ``!sub`` resolver will not work without
a list argument. It does **not** directly reference variables without you directly passing them
in the second list item in its argument.

You *can* combine Jinja2 syntax with this resolver if you want to interpolate in other variables
that Jinja2 has access to.

Example:

.. code-block:: yaml

   parameters:
     ConnectionString: !sub
       # Notice the double-curly braces. That's Jinja2 syntax. Jinja2 will render the username into
       # the string even before the yaml is loaded. If you use Jinja2 to interpolate the value, then
       # it's not a template string variable you need to pass in the second list item passed to
       # !sub.
       - "postgres://{{ var.username }}:{password}@{hostname}:{port}/{{ stack_group_config.database }}"
       - password: !ssm /my/ssm/password
         hostname: !stack_output my/database/stack.yaml::HostName
         port: !stack_output my/database/stack.yaml::Port

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

Calling AWS services in your custom resolver
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For details on calling AWS services or invoking AWS-related third party tools in your resolver, see
:ref:`using_connection_manager`


Resolver arguments
^^^^^^^^^^^^^^^^^^
Resolver arguments can be a simple string or a complex data structure. You can even use
other resolvers in the arguments to resolvers! (Note: Other resolvers can only be passed in
arguments when they're passed in lists and dicts.)

.. code-block:: yaml

   template:
     path: <...>
     type: <...>
   parameters:
     Param1: !ssm "/dev/DbPassword"
     Param2: !ssm {"name": "/dev/DbPassword"}
     Param3: !ssm
       name: "/dev/DbPassword"
     Param4: !ssm
       name: !stack_output my/other/stack.yaml::MySsmParameterName

.. _Custom Resolvers: #custom-resolvers
.. _this is great place to start: https://docs.python.org/3/distributing/

Resolving to nothing
^^^^^^^^^^^^^^^^^^^^
When a resolver returns ``None``, this means that it resolves to "nothing". For resolvers set for
single values (such as for ``template_bucket_name`` or ``cloudformation_service_role``), this just means the value is
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
operating on that Stack Config. These commands include ``dump template``, ``validate``, and ``diff``.
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
  ``!stack_output other_stack.yaml::OutputName`` and you run the ``dump template`` command, the generated
  template will replace that value with ``"StackOutputotherstackyamlOutputName"``. This isn't as
  "pretty" as the sort of placeholder used for stack parameters, but the use of sceptre_user_data is
  broader, so it placeholder values can only be alphanumeric to reduce chances of it breaking the
  template.
* Resolvable properties that are *always* used when performing template operations (like ``sceptre_role``
  and ``template_bucket_name``) will resolve to ``None`` and not be used for those operations if they
  cannot be resolved.

Any command that allows these placeholders can have them disabled with the ``--no-placeholders`` ClI
option.
