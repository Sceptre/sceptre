---
layout: docs
title: CLI Guide
---

# Command Line Interface

Sceptre can be used as a command line tool. Sceptre commands take the format:

```
$ sceptre [OPTIONS] COMMAND [ARGS]
```

Running Sceptre without a subcommand will display help, showing a list of the
available commands.

## Autocomplete

If you are using Bash you can enable autocomplete by entering the following
command `eval "$(_SCEPTRE_COMPLETE=source sceptre)"`. Autocomplete will work
for subcommands and parameters.

## Options

```
  --version                  Show the version and exit.
  --debug                    Turn on debug logging.
  --dir TEXT                 Specify sceptre directory.
  --output [yaml|json]       The formatting style for command output.
  --no-colour                Turn off output colouring.
  --var TEXT                 A variable to template into config files.
  --var-file FILENAME        A YAML file of variables to template into config
                             files.
  --ignore-dependencies      Ignore dependencies when executing command.
  --help                     Show this message and exit.
```

## Commands

The available commands are:

```
  create         Creates a stack or a change set.
  delete         Deletes a stack or a change set.
  describe       Commands for describing attributes of stacks.
  estimate-cost  Estimates the cost of the template.
  execute        Executes a Change Set.
  generate       Prints the template.
  launch         Launch a Stack or StackGroup.
  list           Commands for listing attributes of stacks.
  new            Commands for initialising Sceptre projects.
  set-policy     Sets Stack policy.
  status         Print status of stack or stack_group.
  update         Update a stack.
  validate       Validates the template.
```

## Command Options

Command options differ depending on the command, and can be found by running:

```shell
$ sceptre COMMAND --help
```

## Export Stack Outputs to Environment Variables

Stack outputs can be exported as environment variables with the command:

```shell
$ eval $(sceptre --ignore-dependencies list outputs STACKGROUP/STACK.yaml --export=envvar)
```

Note that Sceptre prepends the string `SCEPTRE_` to the name of the environment
variable:

```shell
$ env | grep SCEPTRE

SCEPTRE_<output_name>=<output_value>
```
