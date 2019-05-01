Get Started
===========

Install
-------

This tutorial assumes that you have installed Sceptre. Instructions on how to
do this can be found in the section on :doc:`installing Sceptre <install>`.

Directory Structure
-------------------

``sceptre new`` provides a quick and easy way to setup a Sceptre project.

To setup a fresh project run:

.. code-block:: text

   $ sceptre new project my-sceptre-project

   Please enter a region []:
   Please enter a project_code [my-sceptre-project]:

This will produce the following directory structure:

.. code-block:: text

   tree
   .
   my-sceptre-project
       ├── config
       │   └── config.yaml
       └── templates

The ``config`` directory is where you will keep the configuration for your
Stacks and the ``templates`` directory is where you will keep your
CloudFormation templates.

Lets add our first template and stack config. We are going to create a
``StackGroup`` (directory) called ``dev`` and setup a Stack with a single
``VPC`` in it.

On \*nix systems:

.. code-block:: text

   mkdir config/dev
   touch config/dev/config.yaml config/dev/vpc.yaml templates/vpc.json

``vpc.json`` will contain a CloudFormation template, ``vpc.yaml`` will contain
config relevant to that template, and ``config.yaml`` will contain environment
config.

Our First Template - vpc.json
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add the following CloudFormation to ``templates/vpc.json``:

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

For more information on CloudFormation, see the AWS documentation on
`CloudFormation`_.

Our First StackGroup config - config.yaml
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add the following configuration to ``config/dev/config.yaml``:

.. code-block:: yaml

   project_code: sceptre-example
   region: eu-west-1

Sceptre prefixes stack names with the ``project_code``. All resources in this
StackGroup will be built in the AWS region ``region``.

Our First Stack config - vpc.yaml
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add the following configuration to ``config/dev/vpc.yaml``:

.. code-block:: yaml

   template_path: vpc.json
   parameters:
     CidrBlock: 10.0.0.0/16

``template_path`` specifies the relative path to the CloudFormation, Python or
Jinja2 template to use to launch the Stack. Sceptre will use the ``templates``
directory as the root templates directory to base your ``template_path`` from.

``parameters`` lists the parameters which are supplied to the template
``vpc.json``.

You should now have a Sceptre project that looks a bit like:

.. code-block:: text

   tree
   .
   ├── config
   │   ├── config.yaml
   │   └── dev
   │       ├── config.yaml
   │       └── vpc.yaml
   └── templates
       └── vpc.json

..

   Note: You do not need to make sure the Template and Stack config names
   match, since you define the ``template_path`` in your Stack config, but it
   can be useful to keep track of what is going on.

You will also notice that we have two ``config.yaml`` files, one in ``config/``
and the other in ``config/dev``. We will explain this later but Sceptre will
eventually merge these two files when generating the overall config file where
values from the child configs replace the parent (unless otherwise specified).

Commands
--------

Create stack
~~~~~~~~~~~~

We can create the VPC Stack with the following command:

.. code-block:: text

   $ sceptre create dev/vpc.yaml

This command must be run from the ``my-sceptre-project`` directory.

Meta commands
~~~~~~~~~~~~~

We can find out information about our running stack:

.. code-block:: text

   $ sceptre list resources dev
   $ sceptre list resources dev/vpc.yaml
   $ sceptre --ignore-dependencies list outputs dev/vpc.yaml

Update stack
~~~~~~~~~~~~

If the Stack’s config or Template is changed in ``vpc.yaml``, the Stack can be
updated with:

.. code-block:: text

   $ sceptre update dev/vpc.yaml

Delete stack
~~~~~~~~~~~~

Delete the stack:

.. code-block:: text

   $ sceptre delete dev/vpc.yaml

Next Steps
----------

We have created our first Sceptre project, added a Template and Stack config,
and used the CLI to create, update and delete the Stack. You can find a full
reference to the CLI :doc:`in our CLI guide <cli>`


.. _CloudFormation: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html
