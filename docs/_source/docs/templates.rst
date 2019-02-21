Templates
=========

Sceptre uses CloudFormation Templates to launch AWS Stacks. Templates must be
stored in a directory named ``templates/``, in the same directory as the
``config/`` directory:

.. code-block:: text

   .
   ├── config
   │   └── dev
   │       ├── config.yaml
   │       └── vpc.yaml
   └── templates
       └── vpc.py

CloudFormation
--------------

Templates with ``.json`` or ``.yaml`` extensions are treated as CloudFormation
Templates. They are read in and used without modification.

Jinja
-----

{% raw %} Templates with ``.j2`` extensions are treated as Jinja2 Templates.
These are rendered and should create a raw JSON or YAML CloudFormation
Template. Sceptre User Data is accessible within Templates as
``sceptre_user_data``. For example ``{{ sceptre_user_data.some_variable }}``.
``sceptre_user_data`` accesses the ``sceptre_user_data`` key in the Stack
Config file. {% endraw %}

Python
------

Templates with a ``.py`` extension are treated as Python Templates. They should
implement a function named ``sceptre_handler(sceptre_user_data)`` which returns
the CloudFormation Template as a ``string``. Sceptre User Data is passed to
this function as an argument. If Sceptre User Data is not defined in the Stack
Config file, Sceptre passes an empty ``dict``.

Example
~~~~~~~

This example is using `troposphere`_
to generate CloudFormation Template as a `json` string.

.. code-block:: python

    from troposphere import Template
    from troposphere.ec2 import VPC

    def vpc(sceptre_user_data):
        """AWS VPC CloudFormationTemplate"""
        template = Template()
        template.add_resource(VPC(
                "VirtualPrivateCloud",
                CidrBlock=sceptre_user_data["cidr_block"]
            ))
        return template.to_yaml()

    def sceptre_handler(sceptre_user_data):
        return vpc(sceptre_user_data)

.. _troposphere: https://github.com/cloudtools/troposphere/