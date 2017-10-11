---
layout: docs
---

# Command Line Interface

Sceptre can be used as a command line tool. Sceptre commands take the format:

```
$ sceptre [GLOBAL_OPTIONS] COMMAND [ARGS] [COMMAND_OPTIONS]
```

Running sceptre without a subcommand will display help, showing a list of the available commands.

## Global Options

- `--debug`: Turn on debug logging.
- `--dir`: Specify the sceptre directory with an absolute or relative path.
- `--no-colour`: Disable coloured output.
- `--output`: Specify the output format. Available formats: `[yaml, json]`.
- `--var`: Overwrite an arbitrary config item. For more information, see the section on [Templating]({{ site.baseurl }}/docs/environment_config.html#templating).
- `--var-file`: Overwrite arbitrary config item(s) with data from a variables file. For more information, see the section on [Templating]({{ site.baseurl }}/docs/environment_config.html#templating).


## Commands

The available commands are:

```
$ sceptre continue-update-rollback
$ sceptre create-change-set
$ sceptre create-stack
$ sceptre delete-change-set
$ sceptre delete-env
$ sceptre delete-stack
$ sceptre describe-change-set
$ sceptre describe-env
$ sceptre describe-env-resources
$ sceptre describe-stack-outputs
$ sceptre describe-stack-resources
$ sceptre diff
$ sceptre execute-change-set
$ sceptre generate-template
$ sceptre get-stack-policy
$ sceptre init
$ sceptre launch-env
$ sceptre launch-stack
$ sceptre list-change-sets
$ sceptre lock-stack
$ sceptre set-stack-policy
$ sceptre unlock-stack
$ sceptre update-stack
$ sceptre update-stack-cs
$ sceptre validate-template
```


## Command Options

Command options differ depending on the command, and can be found by running:

```shell
$ sceptre COMMAND --help
```


## Export Stack Outputs to Environment Variables

Stack outputs can be exported as environment variables with the command:

```shell
$ eval $(sceptre describe-stack-outputs ENVIRONMENT STACK --export=envvar)
```

Note that Sceptre prepends the string `SCEPTRE_` to the name of the environment variable:

```shell
$ env | grep SCEPTRE
SCEPTRE_<output_name>=<output_value>
```
