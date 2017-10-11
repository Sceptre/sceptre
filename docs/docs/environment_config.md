---
layout: docs
---

# Environment Config

Environment config stores information related to the environment, such as a particular IAM role to assume, the name of the S3 bucket in which to store templates, and the target region in which to build resources. Environment config is stored in various files around the directory structure, all with the name `config.yaml`.

## Structure

An environment config file is a yaml object of key-value pairs configuring Sceptre. The available keys are listed below.

- [iam_role](#iam_role) *(optional)*
- [project_code](#project_code) *(required)*
- [region](#region) *(required)*
- [template_bucket_name](#template_bucket_name) *(optional)*
- [template_key_prefix](#template_key_prefix) *(optional)*
- [require_version](#require_version) *(optional)*

Sceptre only checks for and uses the above keys in environment config files, but any others added by the user are read in and are made available to the user via the `sceptre.environment.Environment().config` attribute.


### iam_role

The ARN of a role for Sceptre to assume before interacting with the environment. If not supplied, Sceptre uses the user's AWS CLI credentials.


### project_code

A code which is prepended to the stack names of all stacks built by Sceptre.


### region

The AWS region to build stacks in. Sceptre should work in any [region which supports CloudFormation](http://docs.aws.amazon.com/general/latest/gr/rande.html#cfn_region).


### template\_bucket\_name

The name of an S3 bucket to upload CloudFormation Templates to. Note that S3 bucket names must be globally unique. If the bucket does not exist, Sceptre creates one using the given name, in the AWS region specified by `region`.

If this parameter is not added, Sceptre does not upload the template to S3, but supplies the template to Boto3 via the `TemplateBody` argument. Templates supplied in this way have a lower maximum length, so using the `template_bucket_name` parameter is recommended.


### template\_key\_prefix

A string which is prefixed onto the key used to store templates uploaded to S3. Templates are stored using the key:

```
<template_key_prefix>/<region>/<environment>/<stack_name>-<timestamp>.<extension>
```

Template key prefix can contain slashes ("/"), which are displayed as directories in the S3 console.

Extension can be `json` or `yaml`.

Note that if `template_bucket_name` is not supplied, this parameter is ignored.


### require_version

A [PEP 440](https://www.python.org/dev/peps/pep-0440/#version-specifiers) compatible version specifier. If the Sceptre version does not fall within the given version requirement it will abort.


## Cascading Config

Using Sceptre, config files can be cascaded. Given the following sceptre directory structure:

```
.
└── config
    ├── account-1
    │   ├── config.yaml
    │   └── dev
    │       └── config.yaml
    └── config.yaml
```

General configurations should be defined at a high level, and more specific configurations should be defined at a lower directory level. YAML files which define configuration settings with names which overlap will take precedence if they are deeper in the directory structure. For example, if you wanted the dev environment to build to a different region, this setting could be specified in the config/dev/config.yaml file, and would only be applied to builds in the dev environment.

In the above directory structure, `config/config.yaml` will be read in first, followed by `config/account-1/config.yaml`, followed by `config/account-1/dev/config.yaml`. Config files read in later overwrite any key-value pairs shared by those previously read in. Thus general config can be defined at a high level, and more specific config can be defined at a lower directory level.


## Templating

Sceptre supports the use of templating in config files. Templating allows config files to be further configured using values from the command line, environment variables, files or parts of the environment path.

Internally, Sceptre uses Jinja2 for templating, so any valid Jinja2 syntax should work with Sceptre templating.

Templating can be used for any values in the config files, not just those that are used by Sceptre.


### Var

User variables are used to replace the value of any item in a config file with a value defined by a cli flag or in a YAML variable file:

```yaml
iam_role: {% raw %}{{ var.iam_role }}{% endraw %}
region: eu-west-1
```

This item can be set using either a command line flag:

```shell
$ sceptre --var "iam_role=<your iam role>" <COMMAND>
```

Or from a YAML variable file:

```shell
$ sceptre --var-file=variables.yaml <COMMAND>
```

where `variables.yaml` contains::

```yaml
iam_role: <your iam role>
```

The `--var` flag can be used multiple times to supply multiple variables. If both `--var` and `--var-file` are supplied, `--var` overwrites any common values in `--var-file`.

For command line flags, Sceptre splits the string on the first equals sign "=", and sets the key to be the first substring, and the value to be the second. Due to the large number of possible user inputs, no error checking is performed on the value of the --var flag, and it is the user's responsibility to make sure that the value is correctly formatted.

All user variables are supplied to all config files, so users must be careful to make sure that user variable names do not unintentionally clash.


### Environment Variables

Config item values can be replaced with environment variables:

```yaml
iam_role: {% raw %}{{ environment_variable.IAM_ROLE }}{% endraw %}
region: eu-west-1
```

Where `IAM_ROLE` is the name of an environment variable.


### Environment Path

Config item values can be replaced with parts of the environment path:

```yaml
region: {% raw %}{{ environment_path.0 }}{% endraw %}
iam_role: role
```

Where the value is taken from the first part of the environment path from the invoking sceptre command:

```shell
$ sceptre launch-stack eu-west-1/dev vpc
```


### Template Defaults

Any templated value can be supplied with a default value with the syntax:

```jinja2
{% raw %}{{ var.value | default("default_value") }}{% endraw %}
```

### String Manipulation

Variables are rendered by Jinja2 and so can have their case change, can be sliced, split or combined with other strings

```jinja2
{% raw %}
bucket_name: {{ environment_path.0.lower() }}-{{ environment_path.1.lower() }}-assets
object_path: {{ environment_path.0.0 }}/{{ environment_path.1[-1] }}/{{ var.value.split("_")[-1] }}/dont/do/this/
{% endraw %}
```

## Examples

```yaml
iam_role: arn:aws:iam::123456789012:role/sceptrerole
project_code: prj
region: eu-west-1
template_bucket_name: sceptre-artifacts
template_key_prefix: my/prefix
```

```yaml
{% raw %}
iam_role: {{ var.iam_role }}
project_code: {{ var.project_code | default("prj") }}
region: {{ environment_path.2 }}
template_bucket_name: {{ environment_variable.TEMPLATE_BUCKET_NAME }}
{% endraw %}
```
