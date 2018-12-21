About
=====

Sceptre is a tool to drive CloudFormation. Sceptre manages the creating,
updating and deletion of stacks, and provides meta commands to allow users to
get information about their stacks. Sceptre is unopinionated, enterprise ready
and designed to be run as part of CI/CD pipelines. Sceptre is accessible as a
CLI tool, or as a Python module.

Motivation
----------

CloudFormation lacks a robust tool to deploy and manage stacks. The AWS CLI and
Boto3 both provide some functionality, but neither offer the chaining of one
stack’s outputs to another’s parameters or easy support for working with role
assumes or in multiple accounts, all of which are common tasks when deploying
infrastructure.

Sceptre was developed to produce a single tool which can be used to deploy any
and all CloudFormation.

Overview
--------

Sceptre is used by defining CloudFormation, Jinja2 or Python templates, and
corresponding YAML configuration files. The configuration files include which
account and region to use, and the parameters to be supplied to the templates.

For a tutorial on using Sceptre, see `Get Started`_, or find out more
information about Sceptre below.

Code
----

Sceptre’s source code can be found on `Github`_.

Bugs and feature requests should be raised via our `Issues`_ page.

.. _Get Started: %7B%7B%20site.baseurl%20%7D%7D/docs/get_started.html
.. _Github: https://github.com/cloudreach/sceptre/
.. _Issues: https://github.com/cloudreach/sceptre/issues
