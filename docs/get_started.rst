.. highlight:: shell

===========
Get Started
===========

Install Sceptre
---------------

This tutorial assumes that you have installed Sceptre. Instructions on how to do this are found in the section on :ref:`installation`.

Sceptre Directory Structure
---------------------------

Create the following directory structure in a clean directory named ``sceptre-example``:
::

  .
  ├── config
  │   └── dev
  │       ├── config.yaml
  │       └── vpc.yaml
  └── templates
      └── vpc.json

On Unix systems, this can be done with the following commands::

  $ mkdir config config/dev templates
  $ touch config/dev/config.yaml config/dev/vpc.yaml templates/vpc.json

``vpc.json`` will contain a CloudFormation template, ``vpc.yaml`` will contain config relevant to that template, and ``config.yaml`` will contain environment config.


vpc.json
--------

Add the following CloudFormation to ``vpc.json``:

.. code-block:: json

  {
    "Parameters": {
      "CidrBlock": {
        "Type": "String"
      }
    },
    "Resources": {
      "VPC": {
        "Type": "AWS::EC2::VPC",
        "Properties": {
          "CidrBlock": {
            "Ref": "CidrBlock"
          }
        }
      }
    },
    "Outputs": {
      "VpcId": {
        "Value": {
          "Ref": "VPC"
        }
      }
    }
  }


For more information on CloudFormation, see the AWS documentation on `CloudFormation <http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html>`_.


config.yaml
-----------

Add the following config to ``config.yaml``:

.. code-block:: yaml

  project_code: sceptre-example
  region: eu-west-1

Sceptre prefixes stack names with the ``project_code``. Resources will be built in the AWS region ``region``.


vpc.yaml
--------

Add the following config to ``vpc.yaml``:

.. code-block:: yaml

  template_path: templates/vpc.yaml
  parameters:
    CidrBlock: 10.0.0.0/16


``template_path`` specifies the relative path to the CloudFormation or Troposphere template to use to launch the stack.

``parameters`` lists the parameters which should be supplied by Sceptre to the CloudFormation or Troposphere template.


Create Stack
------------

We can create the VPC stack with the following command::

  $ sceptre create-stack dev vpc

This command must be run from the ``sceptre-examples`` directory.


Meta-Commands
-------------

We can find out information about our running stack::

  $ sceptre describe-env-resources dev
  $ sceptre describe-stack-resources dev vpc
  $ sceptre describe-stack-outputs dev vpc


Update-Stack
------------

If the stack's config or template is changed in vpc.yaml, the stack can be updated with::

  $ sceptre update-stack dev vpc


Delete Stack
------------

Delete the stack::

  $ sceptre delete-stack dev vpc


Next Steps
----------

Full details about Sceptre's capabilities can be found in the full documentation.
