---
layout: docs
title: FAQ
---

# FAQ


## How do I set AWS region or IAM role via the CLI?

These configuration items, and others, can be set from the CLI using [templating]({{ site.baseurl }}/docs/environment_config.html#templating). The syntax for setting the AWS region is presented below. The syntax for replacing the other items is the same, with the word `region` substituted out.

In config.yaml:

```yaml
{% raw %}region: {{ var.region }}{% endraw %}
```

On the CLI:

```shell
$ sceptre --var "region=<your region name>" COMMAND
```


## Should I use a Parameter or Sceptre User Data?

Parameters are the standard way of passing environment-specific configuration to a CloudFormation template. They offer:

- Native support from CloudFormation
- A high degree of customisability, as described in the [AWS documentation](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/parameters-section-structure.html)

However, parameters suffer from the following limitation:

- They cannot alter the template based on the parameter value

Sceptre user data was added to fix this limitation. It is configuration that is passed directly to a template, and so can be used to change the template based on the configuration item's value.

For example, if the Sceptre user data item `number_of_azs` is passed to a subnet tier template, the value could be used to create different numbers of subnets. This cannot be done with native parameters.

In general, native CloudFormation parameters should be used in almost all cases. Sceptre user data should only be used when the user wants to alter the template based on the value of a config value.


## Why are there two ways to supply environment variables in stack config files?

It is possible to replace values in stack config files with environment variables in two ways.

The first is by using templating, and the syntax `{% raw %}{{ environment_variable.VALUE }}{% endraw %}`. Any value in a config file may be replaced using this method.

The second is by using a resolver, and the syntax::

```yaml
parameters:
    param_1: !environment_variable VALUE
```

This second syntax is only able to replace parameter values.

The difference between these two methods lies in when the value of the environment variable is obtained. The templating method obtains the environment variable when Sceptre is first invoked. The resolver method obtains the environment variable just before the operations `create-stack`, `update-stack`, `launch-stack`, `launch-env`, or `create-change-set` operation is executed (Note that these are the only commands which require parameters). This difference becomes most apparent with the use of the `launch-env` command. As multiple stacks are launched, early stacks can set environment variables (using Hooks) which can then be read in by later stacks. This is only possible using resolvers.

In order to use environment variables set by Hooks run by a stack previously built in the same `launch-env` command, the environment variable resolver must be used.
