============
Introduction
============

About
-----

Sceptre is a tool to drive Cloudformation. Sceptre manages the creating, updating and deletion of stacks, and provides meta commands to allow users to get information about their stacks. Sceptre is unopinionated, enterprise ready and designed to be run as part of CI/CD pipelines. Sceptre is accessible as a CLI tool, or as a Python module.


Motivation
----------

CloudFormation lacks a robust tool to deploy and manage stacks. The AWS CLI and Boto3 both provide some functionality, but neither offer the chaining of one stack's outputs to another's parameters or easy support for working with role assumes or in multiple accounts, all of which are common tasks when deploying infrastructure.

Sceptre was developed to produce a single tool which can be used to deploy any and all CloudFormation. It is intended to replace boilerplate scripts currently used.


Overview
--------

Sceptre is used by defining CloudFormation or Troposphere templates, and corresponding YAML config files. The config files include which account and region to use, and the parameters to be supplied to the templates.

For a tutorial on using Sceptre, see Get Started, or find out more information about Sceptre below.


Code
----

Sceptre's source code can be found on `BitBucket <https://bitbucket.org/cloudreach/sceptre/>`_. Note that the source code is currently closed source, and will only be visible to Cloudreach employees.

Bugs and feature requests should be raised via our `Issues <https://bitbucket.org/cloudreach/sceptre/issues?status=new&status=open>`_ page.
