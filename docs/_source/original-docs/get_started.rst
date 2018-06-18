Get Started
===========

Install
-------

This tutorial assumes that you have installed Sceptre. Instructions on how to do this are found in the section on `installation <%7B%7B%20site.url%20%7D%7D%7B%7B%20site.baseurl%20%7D%7D/docs/install.html>`__.

Directory Structure
-------------------

Create the following directory structure in a clean directory named ``sceptre-example``:

.. code-block:: text

   .
   ├── config
   │   └── dev
   │       ├── config.yaml
   │       └── vpc.yaml
   └── templates
       └── vpc.json

On Unix systems, this can be done with the following commands:

.. code-block:: shell

   $ mkdir config config/dev templates
   $ touch config/dev/config.yaml config/dev/vpc.yaml templates/vpc.json

``vpc.json`` will contain a CloudFormation template, ``vpc.yaml`` will contain config relevant to that template, and ``config.yaml`` will contain environment config.

vpc.json
~~~~~~~~

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

For more information on CloudFormation, see the AWS documentation on `CloudFormation <http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html>`__.

config.yaml
~~~~~~~~~~~

Add the following config to ``config.yaml``:

.. code-block:: yaml

   project_code: sceptre-example
   region: eu-west-1

Sceptre prefixes stack names with the ``project_code``. Resources will be built in the AWS region ``region``.

vpc.yaml
~~~~~~~~

Add the following config to ``vpc.yaml``:

.. code-block:: yaml

   template_path: templates/vpc.json
   parameters:
       CidrBlock: 10.0.0.0/16

``template_path`` specifies the relative path to the CloudFormation, Python or Jinja2 template to use to launch the stack.

``parameters`` lists the parameters which should be supplied by Sceptre to the template.

Commands
--------

Create stack
~~~~~~~~~~~~

We can create the VPC stack with the following command:

.. code-block:: shell

   $ sceptre create-stack dev vpc

This command must be run from the ``sceptre-examples`` directory.

Meta commands
~~~~~~~~~~~~~

We can find out information about our running stack:

.. code-block:: shell

   $ sceptre describe-env-resources dev
   $ sceptre describe-stack-resources dev vpc
   $ sceptre describe-stack-outputs dev vpc

Update stack
~~~~~~~~~~~~

If the stack’s config or template is changed in vpc.yaml, the stack can be updated with:

.. code-block:: shell

   $ sceptre update-stack dev vpc

Delete stack
~~~~~~~~~~~~

Delete the stack:

.. code-block:: shell

   $ sceptre delete-stack dev vpc

Next Steps
----------

Further details can be found in the full `documentation <%7B%7B%20site.url%20%7D%7D%7B%7B%20site.baseurl%20%7D%7D/docs>`__.
