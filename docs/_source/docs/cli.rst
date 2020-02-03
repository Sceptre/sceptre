Command Line Interface
======================

Sceptre can be used as a command line tool.
Running Sceptre without a sub-command will display help, showing a list of the
available commands.

Running Sceptre without a subcommand will display help, showing a list of the
available commands.

Autocomplete
------------

To enable CLI autocomplete for subcommands and parameters execute the
following command:

+----------+------------------------------------------------+
| shell    | command                                        |
+==========+================================================+
| bash     | eval "$(_SCEPTRE_COMPLETE=source sceptre)"     |
+----------+------------------------------------------------+
| zsh      | eval "$(_SCEPTRE_COMPLETE=source_zsh sceptre)" |
+----------+------------------------------------------------+

Export Stack Outputs to Environment Variables
---------------------------------------------

Stack outputs can be exported as environment variables with the command:

``eval $(sceptre --ignore-dependencies list outputs STACKGROUP/STACK.yaml --export=envvar)``

Note that Sceptre prepends the string ``SCEPTRE_`` to the name of the
environment variable:

.. code-block:: text

   env | grep SCEPTRE
   SCEPTRE_<output_name>=<output_value>

Variable Handling
-----------------

You can pass variables into your project using ``--var-file`` and ``--var``.

Varibles passed in with ``--var`` will overwrite any matching variables specified in
``--var-file``. If you use multiple ``--var`` flags then the right-most ``--var`` will
overwrite any matching ``--vars`` to the left. For example, in the following command

``sceptre --var var1=one --var var2=two --var var1=three launch stack``

``var1`` will equal ``three``.

You can also use ``--var`` to overwrite nested keys in a ``--var-file``. For example,
given a variable file "vars.yaml":

.. code-block:: yaml

  # vars.yaml
  ---
  top:
    middle:
      nested: hello
    middle2:
      nested: world

we could overwrite ``nested: world`` to ``nested: hi`` using:

``sceptre --var-file vars.yaml --var top.middle2.nested=hi launch stack``

.. note::
  Sceptre will load your entire project to build a full dependency graph.
  This means that all stacks that use variables will need to have a value
  provided to them - even if they are not in your ``command_path`` or are not
  a dependency. Using a --var-file with all variables set can help meet this
  requirement.

Command reference
-----------------

Command options differ depending on the command, and can be found by running:

.. code-block:: text

   sceptre
   sceptre --help
   sceptre COMMAND --help


.. click:: sceptre.cli:cli
  :prog: sceptre
  :show-nested:
