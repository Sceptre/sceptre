.. highlight:: shell

============
Command Line
============

Sceptre can be used as a command line tool. Sceptre commands take the format::

  $ sceptre [GLOBAL_OPTIONS] COMMAND [ARGS] [COMMAND_OPTIONS]

Running sceptre without a subcommand will display help, showing a list of the available commands.

Global Options
--------------

``--debug/--no-debug``: Turn on debug logging.

``--dir``: Specify sceptre directory via absolute or relative path.

``--no-colour``: Disable coloured stdout.

``--output``: Specify the output format. Available formats: ``[yaml, json]``.

``--var``: Overwrite an arbitrary config item. For more information, see the section on :ref:`templating`.

``--var-file``: Overwrite arbitrary config item(s) with data from a variables file. For more information, see the section on :ref:`templating`.


Commands
--------

The available commands are::

  $ sceptre continue-update-rollback
  $ sceptre create-change-set
  $ sceptre create-stack
  $ sceptre delete-change-set
  $ sceptre delete-env
  $ sceptre delete-stack
  $ sceptre describe-env
  $ sceptre describe-change-set
  $ sceptre describe-env-resources
  $ sceptre describe-stack-outputs
  $ sceptre describe-stack-resources
  $ sceptre execute-change-set
  $ sceptre generate-template
  $ sceptre get-stack-policy
  $ sceptre launch-env
  $ sceptre launch-stack
  $ sceptre list-change-sets
  $ sceptre lock-stack
  $ sceptre set-stack-policy
  $ sceptre unlock-stack
  $ sceptre update-stack-cs
  $ sceptre update-stack
  $ sceptre validate-template


Command Options
---------------

Command options differ depending on the command, and can be found by running::

  $ sceptre COMMAND --help


Export Stack Outputs to Environment Variables
---------------------------------------------

Stack outputs can be exported as environment variables with the command::

  $ eval $(sceptre describe-stack-outputs ENVIRONMENT STACK --export=envvar)

Note that Sceptre prepends the string "SCEPTRE_" to the name of the environment variable::
  $ env | grep SCEPTRE
  SCEPTRE_<output_name>=<output_value>
