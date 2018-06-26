Command Line Interface
======================

Sceptre can be used as a command line tool. Sceptre commands take the
format:

.. code:: shell

    $ sceptre

Running sceptre without a subcommand will display help, showing a list
of the available commands.

.. code:: shell

    $ sceptre COMMAND --help

Export Stack Outputs to Environment Variables
---------------------------------------------

Stack outputs can be exported as environment variables with the command:

.. code:: shell

    $ eval $(sceptre describe-stack-outputs ENVIRONMENT STACK --export=envvar)

Note that Sceptre prepends the string ``SCEPTRE_`` to the name of the
environment variable:

.. code:: shell

    $ env | grep SCEPTRE
    SCEPTRE_<output_name>=<output_value>


Commands
--------

.. click:: sceptre.cli:cli
  :prog: sceptre
  :show-nested: