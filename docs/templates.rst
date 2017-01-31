.. highlight:: shell
..  _template:

=========
Templates
=========

Sceptre uses CloudFormation or Troposphere templates to launch AWS Stacks. Conventionally, templates are stored in a directory named templates, in the same directory as the config directory::

  .
  ├── config
  │   └── dev
  │       ├── config.yaml
  │       └── vpc.yaml
  └── templates
    └── vpc.py

Note that as a path to the template is supplied in a stack's Stack Config file, templates may be stored at any arbitrary location on disk.


CloudFormation
--------------

Templates with ``.json`` or ``.yaml`` extensions are treated as CloudFormation templates. They are read in and launched without modification.


Troposphere
-----------

Templates with a ``.py`` extension are treated as Troposphere templates. They should implement a function named ``sceptre_handler(sceptre_user_data)`` which returns the CloudFormation template as a ``string``. Sceptre User Data is passed to this function as an argument. If Sceptre User Data is not defined in the Stack Config file, Sceptre passes an empty ``dict``.


Example
```````

.. code-block:: python

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
