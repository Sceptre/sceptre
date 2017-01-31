.. highlight:: python

=============
Python Module
=============

Sceptre can be used as a Python module. Import Sceptre as follows::

  from sceptre.environment import Environment

Initialise an Environment:

.. code-block:: python

  env = Environment(
    sceptre_dir="string",
    environment_path="string",
    options={}
  )

- ``sceptre_dir``: The Sceptre Directory, as described in :ref:`terminology`.
- ``environment_path``: The Environment Path, as described in :ref:`terminology`.
- ``options``: A dict of key-value pairs which can be used to overwrite the key-value pairs read in from the ``config.yaml`` files.

More information can be found at the API specification for :class:`sceptre.environment.Environment`.

A list of an Environment's Stack names can be obtained from::

  env.available_stacks

A particular Stack object can be accessed using the following syntax::

  stack = env.<stack_name>

More information can be found at the API specification for :class:`sceptre.stack.Stack`.


ConnectionManager
-----------------

A Sceptre environment's connection manager can be used, as described in the section :ref:`using_an_environments_connection_manager`.
