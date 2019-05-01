Command Line Interface
======================

Sceptre can be used as a command line tool.
Running Sceptre without a sub-command will display help, showing a list of the
available commands.

Running Sceptre without a subcommand will display help, showing a list of the
available commands.

Autocomplete
------------

If you are using Bash you can enable autocomplete by entering the following
command ``eval "$(_SCEPTRE_COMPLETE=source sceptre)"``. Autocomplete will work
for subcommands and parameters.

Export Stack Outputs to Environment Variables
---------------------------------------------

Stack outputs can be exported as environment variables with the command:

``eval $(sceptre --ignore-dependencies list outputs STACKGROUP/STACK.yaml --export=envvar)``

Note that Sceptre prepends the string ``SCEPTRE_`` to the name of the
environment variable:

.. code-block:: text

   env | grep SCEPTRE
   SCEPTRE_<output_name>=<output_value>

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

