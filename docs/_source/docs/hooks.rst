Hooks
=====

Hooks allows the ability for custom commands to be run when Sceptre actions
occur.

A hook is executed at a particular hook point when Sceptre is run.

If required, users can create their own ``hooks``, as described in the section
`Custom Hooks`_.

Hook points
-----------

``before_create`` or ``after_create`` - run hook before or after Stack creation.

``before_update`` or ``after_update`` - run hook before or after Stack update.

``before_delete`` or ``after_delete`` - run hook before or after Stack deletion.

Syntax:

Hooks are specified in a Stack’s config file, using the following syntax:

.. code-block:: yaml

   hooks:
     hook_point:
       - !command_type command 1
       - !command_type command 2

Available Hooks
---------------

cmd
~~~

Executes the argument string in the shell as a Python subprocess.

For more information about how this works, see the `subprocess documentation`_

Syntax:

.. code-block:: yaml

   <hook_point>:
     - !cmd <shell_command>

Example:

.. code-block:: yaml

   before_create:
     - !cmd "echo hello"

asg_scaling_processes
~~~~~~~~~~~~~~~~~~~~~

Suspends or resumes autoscaling scaling processes.

Syntax:

.. code-block:: yaml

   <hook_point>:
     - !asg_scaling_processes <suspend|resume>::<process-name>

Example:

.. code-block:: yaml

   before_update:
     - !asg_scaling_processes suspend::ScheduledActions

More information on suspend and resume processes can be found in the AWS
`documentation`_.

Examples
--------

A Stack’s ``config.yml`` where multiple hooks with multiple commands are
specified:

.. code-block:: yaml

   template_path: templates/example.py
   parameters:
     ExampleParameter: example_value
   hooks:
     before_create:
       - !cmd "echo creating..."
     after_create:
       - !cmd "echo created"
       - !cmd "echo done"
     before_update:
       - !asg_scaling_processes suspend::ScheduledActions
     after_update:
       - !cmd "mkdir example"
       - !cmd "touch example.txt"
       - !asg_scaling_processes resume::ScheduledActions

Custom Hooks
------------

Users can define their own custom hooks, allowing users to extend hooks and
integrate additional functionality into Sceptre projects.

A hook is a Python class which inherits from abstract base class ``Hook`` found
in the ``sceptre.hooks module``.

Hooks are require to implement a ``run()`` function that takes no parameters
and to call the base class initializer.

Hooks may have access to ``argument``, and ``stack`` as object attributes. For example ``self.stack``.

Sceptre uses the ``sceptre.hooks`` entry point to locate hook classes. Your
custom hook can be written anywhere and is installed as Python package.
In case you are not familiar with python packaging, `this is great place to start`_.

Example
~~~~~~~

The following python module template can be copied and used:

.. code-block:: bash

   custom_hook
   ├── custom_hook.py
   └── setup.py

custom_hook.py
^^^^^^^^^^^^^^

.. code-block:: python

    from sceptre.hooks import Hook

    class CustomHook(Hook):
        """
        The following instance attributes are inherited from the parent class Hook.

        Parameters
        ----------
        argument: str
            The argument is available from the base class and contains the
            argument defined in the Sceptre config file (see below)
        stack: sceptre.stack.Stack
             The associated stack of the hook.
        connection_manager: sceptre.connection_manager.ConnectionManager
            Boto3 Connection Manager - can be used to call boto3 api.

        """
        def __init__(self, *args, **kwargs):
            super(CustomHook, self).__init__(*args, **kwargs)

        def run(self):
            """
            run is the method called by Sceptre. It should carry out the work
            intended by this hook.

            To use instance attribute self.<attribute_name>.

            Examples
            --------
            self.argument
            self.stack_config

            """
            print(self.argument)

setup.py
^^^^^^^^

.. code-block:: python

   from setuptools import setup

   setup(
       name='custom_hook_package',
       py_modules=['<custom_hook_module_name>'],
       entry_points={
           'sceptre.hooks': [
               '<custom_hook_command_name> = <custom_hook_module_name>:CustomHook',
           ],
       }
   )

Then install using ``python setup.py install`` or ``pip install .`` commands.

This hook can be used in a Stack config file with the following syntax:

.. code-block:: yaml

   template_path: <...>
   hooks:
     before_create:
       - !custom_hook_command_name <argument> # The argument is accessible via self.argument

.. _Custom Hooks: #custom-hooks
.. _subprocess documentation: https://docs.python.org/3/library/subprocess.html
.. _documentation: http://docs.aws.amazon.com/autoscaling/latest/userguide/as-suspend-resume-processes.html
.. _this is great place to start: https://docs.python.org/3/distributing/