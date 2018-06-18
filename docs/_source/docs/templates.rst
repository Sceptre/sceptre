Templates
=========

Sceptre uses CloudFormation templates to launch AWS Stacks.
Conventionally, templates are stored in a directory named templates, in
the same directory as the config directory:

::

    .
    ├── config
    │   └── dev
    │       ├── config.yaml
    │       └── vpc.yaml
    └── templates
        └── vpc.py

Note that as a path to the template is supplied in a Stack Config file,
templates may be stored at any arbitrary location on disk.

CloudFormation
--------------

Templates with ``.json`` or ``.yaml`` extensions are treated as
CloudFormation templates. They are read in and used without
modification.

Jinja
-----

Templates with ``.j2`` extensions are treated as Jinja2
templates. These are rendered and should create a raw JSON or YAML
CloudFormation template. Sceptre User Data is accessible within
templates as ``sceptre_user_data``. For example
``{{ sceptre_user_data.some_variable }}``. ``sceptre_user_data``
accesses the ``sceptre_user_data`` key in the Stack Config file.

Python
------

Templates with a ``.py`` extension are treated as Python templates. They
should implement a function named ``sceptre_handler(sceptre_user_data)``
which returns the CloudFormation template as a ``string``. Sceptre User
Data is passed to this function as an argument. If Sceptre User Data is
not defined in the Stack Config file, Sceptre passes an empty ``dict``.

Example
~~~~~~~

.. code:: python

    from troposphere import Template, Parameter, Ref
    from troposphere.ec2 import VPC


    class Vpc(object):
        def __init__(self, sceptre_user_data):
            self.template = Template()
            self.sceptre_user_data = sceptre_user_data
            self.add_vpc()

        def add_vpc(self):
            self.vpc = self.template.add_resource(VPC(
                "VirtualPrivateCloud",
                CidrBlock=self.sceptre_user_data["cidr_block"]
            ))


    def sceptre_handler(sceptre_user_data):
        vpc = Vpc(sceptre_user_data)
        return vpc.template.to_json()
