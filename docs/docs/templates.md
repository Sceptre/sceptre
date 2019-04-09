---
layout: docs
title: Templates
---

# Templates

Sceptre uses CloudFormation Templates to launch AWS Stacks. Templates must be
stored in a directory named `templates/`, in the same directory as the
`config/` directory:

```
.
├── config
│   └── dev
│       ├── config.yaml
│       └── vpc.yaml
└── templates
    └── vpc.py
```

## CloudFormation

Templates with `.json` or `.yaml` extensions are treated as CloudFormation
Templates. They are read in and used without modification.

## Jinja

{% raw %}
Templates with `.j2` extensions are treated as Jinja2 Templates. These are
rendered and should create a raw JSON or YAML CloudFormation Template. Sceptre
User Data is accessible within Templates as `sceptre_user_data`. For example
`{{ sceptre_user_data.some_variable }}`. `sceptre_user_data` accesses the
`sceptre_user_data` key in the Stack Config file.
{% endraw %}

## Python

Templates with a `.py` extension are treated as Python Templates. They should
implement a function named `sceptre_handler(sceptre_user_data)` which returns
the CloudFormation Template as a `string`. Sceptre User Data is passed to this
function as an argument. If Sceptre User Data is not defined in the Stack
Config file, Sceptre passes an empty `dict`.

### Stack Configuration
In addition to `sceptre_user_data`, you can also accept a argument called `stack_configuration` which will provide your Python code with a rendered version of the current Stack being built. This can be very useful for projects that have a requirement to process more than just the `sceptre_user_data` and can be used for validation before a template is even created.

For example, if you wanted to check that the Stack Tags being applied are compliant with an organisation tagging policy you would be able to access these values directly

It can also allow you to programatically create the Parameters that you have specified in a Stack

### Example with sceptre_user_data (required)

```python
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
```

### Example with sceptre_user_data and stack_configuration (optional)

```python
from troposphere import Template, Parameter, Ref
from troposphere.ec2 import VPC


class Vpc(object):
    def __init__(self, sceptre_user_data, stack_configuration):
        self.template = Template()
        self.sceptre_user_data = sceptre_user_data
        self.stack_configuration = stack_configuration
        self.add_vpc()

    def add_parameters(self):

        for parameter in self.stack_configuration['parameters'].keys():
            self.template.add_parameter(Parameter(
                parameter,
                Type="String"
            ))

    def add_vpc(self):
        self.vpc = self.template.add_resource(VPC(
            "VirtualPrivateCloud",
            CidrBlock=self.sceptre_user_data["cidr_block"]
        ))


def sceptre_handler(sceptre_user_data, stack_configuration):
    vpc = Vpc(sceptre_user_data, stack_configuration)
    return vpc.template.to_json()
```
