About
=====

Sceptre is a tool to drive CloudFormation_. Sceptre manages the creation,
update and deletion of stacks while providing meta commands which
allow users to retrieve information about their stacks. Sceptre is
unopinionated, enterprise ready and designed to run as part of CI/CD pipelines.
Sceptre is accessible as a CLI tool or as a Python module.

Motivation
----------

CloudFormation_ lacks a robust tool to deploy and manage stacks. While the
`AWS CLI`_ and Boto3_ both provide some functionality, neither offer:

* Chaining one stack's outputs to another's parameters

* Easy support for working with role assumption or multiple accounts

All of the above are common tasks when deploying infrastructure.

Sceptre was developed to produce a single tool which can be used to deploy any
and all CloudFormation_.

Overview
--------

Sceptre is used by defining CloudFormation, Jinja2 or Python templates, with
corresponding YAML configuration files. The configuration files include which
account and region to use as well as the parameters to supply the templates.

For a tutorial on using Sceptre, see `Get Started`_, or find out more
information about Sceptre below.

Code
----

Sceptre’s source code can be found on `Github`_.

Bugs and feature requests should be raised via our `Issues`_ page.

.. _Get Started: %7B%7B%20site.baseurl%20%7D%7D/docs/get_started.html
.. _Github: https://github.com/cloudreach/sceptre/
.. _Issues: https://github.com/cloudreach/sceptre/issues
.. _CloudFormation: https://aws.amazon.com/cloudformation/
.. _AWS CLI: https://aws.amazon.com/cli/
.. _Boto3: https://aws.amazon.com/sdk-for-python/