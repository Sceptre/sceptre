.. _Hooks:

Hooks
=====

Hooks allows the ability for custom commands to be run when Sceptre
actions occur.

A hook is executed at a particular hook point when Sceptre is run.

If required, users can create their own ``hooks``, as described in the
section `Custom Hooks <#custom-hooks>`__.

Hook points
-----------

``before_create`` or ``after_create`` - run hook before or after stack
creation.

``before_update`` or ``after_update`` - run hook before or after stack
update.

``before_delete`` or ``after_delete`` - run hook before or after stack
deletion.

Syntax:

Hooks are specified in a stack's config file, using the following
syntax:

.. code:: yaml

    hooks:
        hook_point:
            - !command_type command 1
            - !command_type command 2

Available Hooks
---------------

cmd
~~~

Executes the argument string in the shell as a Python subprocess.

For more information about how this works, see the `subprocess
documentation <https://docs.python.org/2/library/subprocess.html>`__

Syntax:

.. code:: yaml

    <hook_point>:
        - !cmd <shell_command>

Example:

.. code:: yaml

    before_create:
        - !cmd "echo hello"

asg\_scaling\_processes
~~~~~~~~~~~~~~~~~~~~~~~

Suspends or resumes autoscaling scaling processes.

Syntax:

.. code:: yaml

    <hook_point>:
        - !asg_scaling_processes <suspend|resume>::<process-name>

Example:

.. code:: yaml

    before_update:
        - !asg_scaling_processes suspend::ScheduledActions

More information on suspend and resume processes can be found in the AWS
`documentation <http://docs.aws.amazon.com/autoscaling/latest/userguide/as-suspend-resume-processes.html>`__.

Examples
--------

A stack's ``config.yml`` where multiple hooks with multiple commands are
specified:

.. code:: yaml

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

Users can define their own custom hooks, allowing users to extend hooks
and integrate additional functionality into Sceptre projects.

A hook is a Python class which inherits from abstract base class
``Hook`` found in the ``sceptre.hooks module``.

Hooks are require to implement a ``run()`` function that takes no
parameters and to call the base class initializer.

Hooks may have access to ``argument``, ``stack_config``,
``environment_config`` and ``connection_manager`` as object attributes.
For example ``self.stack_config``.

Sceptre uses the ``sceptre.hooks`` entry point to locate hook classes.
Your custom hook can be written anywhere and is installed as Python
package.

Example
~~~~~~~

The following python module template can be copied and used:

::

    custom_hook
    ├── custom_hook.py
    └── setup.py

custom\_hook.py
^^^^^^^^^^^^^^^

.. code:: python

    from sceptre.hooks import Hook


    class CustomHook(Hook):

        def __init__(self, *args, **kwargs):
            super(CustomHook, self).__init__(*args, **kwargs)


        def run(self):
            """
            run is the method called by Sceptre. It should carry out the work
            intended by this hook.

            self.argument is available from the base class and contains the
            argument defined in the Sceptre config file (see below)

            The following attributes may be available from the base class:
            self.stack_config  (A dict of data from <stack_name>.yaml)
            self.environment_config  (A dict of data from config.yaml)
            self.connection_manager (A connection_manager)
            """
            print(self.argument)

setup.py
^^^^^^^^

.. code:: python

    from setuptools import setup

    setup(
        name='custom_hook',
        entry_points={
            'sceptre.hooks': [
                'custom_hook = custom_hook:CustomHook',
            ],
        }
    )

Then install using ``python setup.py install`` or ``pip install .``
commands.

This hook can be used in a stack config file with the following syntax:

.. code:: yaml

    template_path: <...>
    hooks:
        before_create:
            - !custom_hook <argument>  # The argument is accessible via self.argument
