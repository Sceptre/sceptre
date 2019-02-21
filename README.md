# Sceptre

![image](https://circleci.com/gh/cloudreach/sceptre.png?style=shield) ![image](https://badge.fury.io/py/sceptre.svg)

# About

Sceptre is a tool to drive [AWS CloudFormation](https://aws.amazon.com/cloudformation).
It automates the mundane, repetitive and error-prone tasks, enabling you to concentrate
on building better infrastructure.

# Features

- Code reuse by separating a Stack's template and its configuration
- Support for templates written in JSON, YAML, Jinja2 or Python DSLs such as Troposphere
- Dependency resolution by passing of Stack outputs to parameters of dependent Stacks
- Stack Group support by bundling related Stacks into logical groups (e.g. dev and prod)
- Stack Group-level commands, such as creating multiple Stacks with a single command
- Fast, highly parallelised builds
- Built in support for working with Stacks in multiple AWS accounts and regions
- Infrastructure visibility with meta-operations such as Stack querying protection
- Support for inserting dynamic values in templates via customisable Resolvers
- Support for running arbitrary code as Hooks before/after Stack builds

# Benefits

- Utilises cloud-native Infrastructure as Code engines (CloudFormation)
- You do not need to manage state
- Simple templates using popular templating syntax - Yaml & Jinja
- Powerful flexibility using a mature programming language - Python
- Easy to integrate as part of a CI/CD pipeline by using Hooks
- Simple CLI and API
- Unopinionated - Sceptre does not force a specific project structure

# Install

`$ pip install sceptre`

More information on installing sceptre can be found in our [Installation Guide](https://sceptre.cloudreach.com/latest/docs/install.html)

# Migrate v1 to v2

We have tried to make the migration to Sceptre v2 as simple as possible. For
information about how to migration your v1 project please see our [Migration
Guide](https://github.com/cloudreach/sceptre/wiki/Migration-Guide:-V1-to-V2)

# V1 End of Life Notice

Support for Version 1 will [end on June 1 2019](https://github.com/cloudreach/sceptre/issues/593).
For new projects we recommend using Version 2.

# Example

Sceptre organises Stacks into "Stack Groups". Each Stack is represented by a
YAML configuration file stored in a directory which represents the Stack Group.
Here, we have two Stacks, `vpc` and `subnets`, in a Stack Group named `dev`:

```
$ tree
.
├── config
│   └── dev
│        ├── config.yaml
│        ├── subnets.yaml
│        └── vpc.yaml
└── templates
    ├── subnets.py
    └── vpc.py
```

We can create a Stack with the `create` command. This `vpc` Stack contains
a VPC.

```
$ sceptre create dev/vpc.yaml

dev/vpc - Creating stack dev/vpc
VirtualPrivateCloud AWS::EC2::VPC CREATE_IN_PROGRESS
dev/vpc VirtualPrivateCloud AWS::EC2::VPC CREATE_COMPLETE
dev/vpc sceptre-demo-dev-vpc AWS::CloudFormation::Stack CREATE_COMPLETE
```

The `subnets` Stack contains a subnet which must be created in the VPC. To do
this, we need to pass the VPC ID, which is exposed as a Stack output of the
`vpc` Stack, to a parameter of the `subnets` Stack. Sceptre automatically
resolves this dependency for us.

```
$ sceptre create dev/subnets.yaml
dev/subnets - Creating stack
dev/subnets Subnet AWS::EC2::Subnet CREATE_IN_PROGRESS
dev/subnets Subnet AWS::EC2::Subnet CREATE_COMPLETE
dev/subnets sceptre-demo-dev-subnets AWS::CloudFormation::Stack CREATE_COMPLETE
```

Sceptre implements meta-operations, which allow us to find out information
about our Stacks:

```
$ sceptre list resources dev/subnets.yaml

- LogicalResourceId: Subnet
  PhysicalResourceId: subnet-445e6e32
  dev/vpc:
- LogicalResourceId: VirtualPrivateCloud
  PhysicalResourceId: vpc-c4715da0
```

Sceptre provides Stack Group level commands. This one deletes the whole `dev`
Stack Group. The subnet exists within the vpc, so it must be deleted first.
Sceptre handles this automatically:

```
$ sceptre delete dev

Deleting stack
dev/subnets Subnet AWS::EC2::Subnet DELETE_IN_PROGRESS
dev/subnets - Stack deleted
dev/vpc Deleting stack
dev/vpc VirtualPrivateCloud AWS::EC2::VPC DELETE_IN_PROGRESS
dev/vpc - Stack deleted
```

> Note: Deleting Stacks will _only_ delete a given Stack, or the Stacks that
> are directly in a given StackGroup. By default Stack dependencies that are
> external to the StackGroup are not deleted.

Sceptre can also handle cross Stack Group dependencies, take the following
example project:

```
$ tree
.
├── config
│   ├── dev
│   │   ├── network
│   │   │   └── vpc.yaml
│   │   ├── users
│   │   │   └── iam.yaml
│   │   ├── compute
│   │   │   └── ec2.yaml
│   │   └── config.yaml
│   └── staging
│       └── eu
│           ├── config.yaml
│           └── stack.yaml
├── hooks
│   └── stack.py
├── templates
│   ├── network.json
│   ├── iam.json
│   ├── ec2.json
│   └── stack.json
└── vars
    ├── dev.yaml
    └── staging.yaml
```

In this project `staging/eu/stack.yaml` has a dependency on the output of
`dev/users/iam.yaml`. If you wanted to create the Stack
`staging/eu/stack.yaml`, Sceptre will resolve all of it's dependencies,
including `dev/users/iam.yaml`, before attempting to create the Stack.

## Usage

Sceptre can be used from the CLI, or imported as a Python package.

## CLI

```
Usage: sceptre [OPTIONS] COMMAND [ARGS]...

  Sceptre is a tool to manage your cloud native infrastructure deployments.

Options:
  --version              Show the version and exit.
  --debug                Turn on debug logging.
  --dir TEXT             Specify sceptre directory.
  --output [yaml|json]   The formatting style for command output.
  --no-colour            Turn off output colouring.
  --var TEXT             A variable to template into config files.
  --var-file FILENAME    A YAML file of variables to template into config
                         files.
  --ignore-dependencies  Ignore dependencies when executing command.
  --help                 Show this message and exit.

Commands:
  create         Creates a stack or a change set.
  delete         Deletes a stack or a change set.
  describe       Commands for describing attributes of stacks.
  estimate-cost  Estimates the cost of the template.
  execute        Executes a Change Set.
  generate       Prints the template.
  launch         Launch a Stack or StackGroup.
  list           Commands for listing attributes of stacks.
  new            Commands for initialising Sceptre projects.
  set-policy     Sets Stack policy.
  status         Print status of stack or stack_group.
  update         Update a stack.
  validate       Validates the template.
```

## Python

Using Sceptre as a Python module is very straightforward. You need to create
a SceptreContext, which tells Sceptre where your project path is and which path
you want to execute on, we call this the "command path".

After you have created a SceptreContext you need to pass this into
a SceptrePlan. On instantiation the SceptrePlan will handle all the required
steps to make sure the action you wish to take on the command path are
resolved.

After you have instantiated a SceptrePlan you can access all the actions you
can take on a Stack, such as `validate()`, `launch()`, `list()` and `delete()`.

```python
from sceptre.context import SceptreContext
from sceptre.plan.plan import SceptrePlan

context = SceptreContext("/path/to/project", "command_path")
plan = SceptrePlan(context)
plan.launch()
```

Full API reference documentation can be found in the [Documentation](https://sceptre.cloudreach.com/latest/docs/index.html)

## Tutorial and Documentation

- [Get Started](https://sceptre.cloudreach.com/latest/docs/get_started.html)
- [Documentation](https://sceptre.cloudreach.com/latest/docs/index.html)

## Contributing

See our [Contributing Guide](CONTRIBUTING.md)
