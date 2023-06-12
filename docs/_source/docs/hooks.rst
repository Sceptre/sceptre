Hooks
=====

Hooks allows the ability for actions to be run when Sceptre actions occur.

A hook is executed at a particular hook point when Sceptre is run.

If required, users can create their own ``hooks``, as described in the section `Custom Hooks`_.

Hook points
-----------

- ``before_create``/``after_create`` - Runs before/after Stack creation.
- ``before_update``/``after_update`` - Runs before/after Stack update.
- ``before_delete``/``after_delete`` - Runs before/after Stack deletion.
- ``before_launch``/``after_launch`` - Runs before/after Stack launch.
- ``before_create_change_set``/``after_create_change_set`` - Runs before/after create change set.
- ``before_validate``/``after_validate`` - Runs before/after Stack validation.
- ``before_diff``/``after_diff`` - Runs before/after diffing the deployed stack with the local
  configuration.
- ``before_drift_detect``/``after_drift_detect`` - Runs before/after detecting drift on the stack.
- ``before_drift_show``/``after_drift_show`` - Runs before/after showing detected drift on the stack.
- ``before_dump_config``/``after_dump_config`` - Runs before/after dumpint the Stack Config.
- ``before_dump_template``/``after_dump_template`` - Runs before/after rendering the stack template.
  This hook point is aliased to ``before/generate``/``after_generate``. This hook point will also
  be triggered when diffing, since the template needs to be generated to diff the template.
- ``before_generate``/``after_generate`` - Runs before/after rendering the stack template. This hook
  point is aliased to ``before_dump_template``/``after_dump_template``.

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

   template:
     path: templates/example.py
     type: file
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

   template:
     path: <...>
     type: <...>
   hooks:
     before_create:
       - !custom_hook_command_name <argument> # The argument is accessible via self.argument

hook arguments
^^^^^^^^^^^^^^
Hook arguments can be a simple string or a complex data structure. You can even use resolvers in
hook arguments, so long as they're nested in a list or a dict.

Assume a Sceptre `copy` hook that calls the `cp command`_:

.. code-block:: yaml

   template:
     path: <...>
     type: <...>
   hooks:
     before_create:
       - !copy "-r from_dir to_dir"
     before_update:
       - !copy {"options":"-r", "source": "from_dir", "destination": "to_dir"}
     after_update:
       - !copy
           options: "-r"
           source: "from_dir"
           destination: !stack_output my/other/stack::CopyDestination

.. _Custom Hooks: #custom-hooks
.. _subprocess documentation: https://docs.python.org/3/library/subprocess.html
.. _documentation: http://docs.aws.amazon.com/autoscaling/latest/userguide/as-suspend-resume-processes.html
.. _this is great place to start: https://docs.python.org/3/distributing/
.. _cp command: http://man7.org/linux/man-pages/man1/cp.1.html

Calling AWS services in your custom hook
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For details on calling AWS services or invoking AWS-related third party tools in your hooks, see
:ref:`using_connection_manager`
