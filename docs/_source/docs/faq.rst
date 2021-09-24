FAQ
===

How do I set AWS Region or Profile via the CLI?
-----------------------------------------------

These configuration items, and others, can be set from the CLI using
:ref:`templating <stack_group_config_templating>`. The syntax for setting the AWS region is presented below. The
syntax for replacing the other items is the same, with the word ``region``
substituted out.

In config.yaml:

.. code-block:: yaml

   region: {{ var.region }}

On the CLI:

.. code-block:: text

    sceptre --var "region=<your region name>" COMMAND

Should I use a Parameter or Sceptre User Data?
----------------------------------------------

Parameters are the standard way of passing StackGroup-specific configuration to
a CloudFormation template. They offer:

-  Native support from CloudFormation
-  A high degree of customisability, as described in the `AWS documentation`_

However, parameters suffer from the following limitation:

-  They cannot alter the template based on the parameter value

Sceptre user data was added to fix this limitation. It is configuration that is
passed directly to a template, and so can be used to change the template based
on the configuration item’s value.

For example, if the Sceptre user data item ``number_of_azs`` is passed to a
subnet tier template, the value could be used to create different numbers of
subnets. This cannot be done with native parameters.

In general, native CloudFormation parameters should be used in almost all
cases. Sceptre user data should only be used when the user wants to alter the
template based on the value of a config value.

.. _faq_stackconfig_env:

Why are there two ways to supply environment variables in stack config files?
-----------------------------------------------------------------------------

It is possible to replace values in stack config files with environment
variables in two ways.

The first is by using templating, and the syntax
``{{ environment_variable.VALUE }}``. Any value in a
config file may be replaced using this method.

The second is by using a resolver, and the syntax:

.. code-block:: yaml

   parameters:
     param_1: !environment_variable VALUE

This second syntax is only able to replace parameter values.

The difference between these two methods lies in when the value of the
environment variable is obtained. The templating method obtains the environment
variable when Sceptre is first invoked. The resolver method obtains the
environment variable just before the operations ``create``, ``update``,
``launch`` operation is executed (Note that these are the only commands which
require parameters). This difference becomes most apparent with the use of the
``launch`` command. As multiple stacks are launched, early stacks can set
environment variables (using Hooks) which can then be read in by later stacks.
This is only possible using resolvers.

In order to use environment variables set by Hooks run by a stack previously
built in the same ``launch`` command, the environment variable resolver must be
used.

.. _AWS documentation: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/parameters-section-structure.html

How do I build a Serverless application using Sceptre and SAM?
--------------------------------------------------------------

There are a few different ways that Sceptre can help create serverless
applications or lambdas.  One approach is to use the `SAM CLI`_ to build
and deploy your SAM templates to an S3 bucket then have Sceptre deploy the
generated SAM template to your AWS account. Examples of this approach can
be found in these projects:

- `Sage-Bionetworks Sceptre lambda github template`_
- `Versant SAM Sceptre skeleton example`_

Another approach is to use the Sceptre `before_launch` hook to run either the
SAM or CFN "package" command to generate the packaged version of the template.

CloudFormation Example:

.. code-block:: yaml

  template_path: generated/lambda-packaged.json
  stack_name: cfn-lambda-example
  hooks:
    before_launch:
      - !cmd >
          aws --profile {{ stack_group_config.profile }} cloudformation package
          --template-file templates/cfn-lambda.yaml
          --s3-bucket {{ stack_group_config.template_bucket_name }}
          --output json
          --output-template-file templates/generated/lambda-packaged.json

SAM Example:

.. code-block:: yaml

  template_path: generated/sam-packaged.yaml
  stack_name: sam-example
  hooks:
    before_launch:
      - !cmd >
          sam package --profile {{ stack_group_config.profile }}
          --s3-bucket {{ stack_group_config.template_bucket_name }}
          --template-file templates/sam-app.yaml
          --output-template-file templates/generated/sam-packaged.yaml

.. _SAM CLI: https://github.com/aws/aws-sam-cli
.. _Sage-Bionetworks Sceptre lambda github template: https://github.com/Sage-Bionetworks-IT/lambda-template
.. _Versant SAM Sceptre skeleton example: https://github.com/Versent/sam-sceptre
