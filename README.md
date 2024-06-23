# Sceptre

[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Sceptre/sceptre/gate.yaml)](https://github.com/Sceptre/sceptre/actions/workflows/gate.yaml)
[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/sceptreorg/sceptre?logo=docker&sort=semver)](https://hub.docker.com/r/sceptreorg/sceptre)
[![PyPI](https://img.shields.io/pypi/v/sceptre?logo=pypi)](https://pypi.org/project/sceptre/)
[![PyPI - Status](https://img.shields.io/pypi/status/sceptre?logo=pypi)](https://pypi.org/project/sceptre/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/sceptre?logo=pypi)](https://pypi.org/project/sceptre/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/sceptre?logo=pypi)](https://pypi.org/project/sceptre/)
[![License](https://img.shields.io/pypi/l/sceptre?logo=apache)](https://github.com/Sceptre/sceptre/blob/master/LICENSE)

## About

Sceptre is a tool to drive
[AWS CloudFormation](https://aws.amazon.com/cloudformation). It automates the
mundane, repetitive and error-prone tasks, enabling you to concentrate on
building better infrastructure.

## Features

- Code reuse by separating a Stack's template and its configuration
- Support for templates written in JSON, YAML, Jinja2 or Python DSLs such as
  Troposphere
- Dependency resolution by passing of Stack outputs to parameters of dependent
  Stacks
- Stack Group support by bundling related Stacks into logical groups (e.g. dev
  and prod)
- Stack Group-level commands, such as creating multiple Stacks with a single
  command
- Fast, highly parallelised builds
- Built in support for working with Stacks in multiple AWS accounts and regions
- Infrastructure visibility with meta-operations such as Stack querying
  protection
- Support for inserting dynamic values in templates via customisable Resolvers
- Support for running arbitrary code as Hooks before/after Stack builds

## Benefits

- Utilises cloud-native Infrastructure as Code engines (CloudFormation)
- You do not need to manage state
- Simple templates using popular templating syntax - Yaml & Jinja
- Powerful flexibility using a mature programming language - Python
- Easy to integrate as part of a CI/CD pipeline by using Hooks
- Simple CLI and API
- Unopinionated - Sceptre does not force a specific project structure

## Install

### Using pip

`$ pip install sceptre`

More information on installing sceptre can be found in our
[Installation Guide](https://docs.sceptre-project.org/latest/docs/install.html)

### Using Docker Image

View our [Docker repository](https://hub.docker.com/repositories/sceptreorg).
Images available from version 2.0.0 onward.

To use our Docker image follow these instructions:

1. Pull the image `docker pull sceptreorg/sceptre:[SCEPTRE_VERSION_NUMBER]` e.g.
   `docker pull sceptreorg/sceptre:2.5.0`. Leave out the version number if you
   wish to run `latest` or run `docker pull sceptreorg/sceptre:latest`.

2. Run the image. You will need to mount the working directory where your
   project resides to a directory called `project`. You will also need to mount
   a volume with your AWS config to your docker container. E.g.

`docker run -v $(pwd):/project -v /Users/me/.aws/:/root/.aws/:ro sceptreorg/sceptre:latest --help`

If you want to use a custom ENTRYPOINT simply amend the Docker command:

`docker run -ti --entrypoint='' sceptreorg/sceptre:latest sh`

The above command will enter you into the shell of the Docker container where
you can execute sceptre commands - useful for development.

If you have any other environment variables in your non-docker shell you will
need to pass these in on the Docker CLI using the `-e` flag. See Docker
documentation on how to achieve this.

## Example

Sceptre organises Stacks into "Stack Groups". Each Stack is represented by a
YAML configuration file stored in a directory which represents the Stack Group.
Here, we have two Stacks, `vpc` and `subnets`, in a Stack Group named `dev`:

```sh
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

We can create a Stack with the `create` command. This `vpc` Stack contains a
VPC.

```sh
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

```sh
$ sceptre create dev/subnets.yaml
dev/subnets - Creating stack
dev/subnets Subnet AWS::EC2::Subnet CREATE_IN_PROGRESS
dev/subnets Subnet AWS::EC2::Subnet CREATE_COMPLETE
dev/subnets sceptre-demo-dev-subnets AWS::CloudFormation::Stack CREATE_COMPLETE
```

Sceptre implements meta-operations, which allow us to find out information about
our Stacks:

```sh
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

```sh
$ sceptre delete dev

Deleting stack
dev/subnets Subnet AWS::EC2::Subnet DELETE_IN_PROGRESS
dev/subnets - Stack deleted
dev/vpc Deleting stack
dev/vpc VirtualPrivateCloud AWS::EC2::VPC DELETE_IN_PROGRESS
dev/vpc - Stack deleted
```

> Note: Deleting Stacks will _only_ delete a given Stack, or the Stacks that are
> directly in a given StackGroup. By default Stack dependencies that are
> external to the StackGroup are not deleted.

Sceptre can also handle cross Stack Group dependencies, take the following
example project:

```sh
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
`dev/users/iam.yaml`. If you wanted to create the Stack `staging/eu/stack.yaml`,
Sceptre will resolve all of it's dependencies, including `dev/users/iam.yaml`,
before attempting to create the Stack.

## Usage

Sceptre can be used from the CLI, or imported as a Python package.

## CLI

```text
Usage: sceptre [OPTIONS] COMMAND [ARGS]...

  Sceptre is a tool to manage your cloud native infrastructure deployments.

Options:
  --version                  Show the version and exit.
  --debug                    Turn on debug logging.
  --dir TEXT                 Specify sceptre directory.
  --output [text|yaml|json]  The formatting style for command output.
  --no-colour                Turn off output colouring.
  --var TEXT                 A variable to replace the value of an item in
                             config file.
  --var-file FILENAME        A YAML file of variables to replace the values
                             of items in config files.
  --ignore-dependencies      Ignore dependencies when executing command.
  --merge-vars               Merge variables from successive --vars and var
                             files.
  --help                     Show this message and exit.

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

Using Sceptre as a Python module is very straightforward. You need to create a
SceptreContext, which tells Sceptre where your project path is and which path
you want to execute on, we call this the "command path".

After you have created a SceptreContext you need to pass this into a
SceptrePlan. On instantiation the SceptrePlan will handle all the required steps
to make sure the action you wish to take on the command path are resolved.

After you have instantiated a SceptrePlan you can access all the actions you can
take on a Stack, such as `validate()`, `launch()`, `list()` and `delete()`.

```python
from sceptre.context import SceptreContext
from sceptre.plan.plan import SceptrePlan

context = SceptreContext("/path/to/project", "command_path")
plan = SceptrePlan(context)
plan.launch()
```

Full API reference documentation can be found in the
[Documentation](https://docs.sceptre-project.org/)

## Tutorial and Documentation

- [Get Started](https://docs.sceptre-project.org/latest/docs/get_started.html)
- [Documentation](https://docs.sceptre-project.org/)

## Communication

Sceptre community discussions happen in the #sceptre chanel in the
[og-aws Slack](https://github.com/open-guides/og-aws).  To join click
on <http://slackhatesthe.cloud/> to create an account and join the
#sceptre channel.

## Contributing

See our [Contributing Guide](CONTRIBUTING.md)

## Sponsors

[![Sage Bionetworks](sponsors/sage_bionetworks_logo.png "Sage Bionetworks")](https://sagebionetworks.org)

[![GoDaddy](sponsors/godaddy_logo.png "GoDaddy")](https://www.godaddy.com)

[![Cloudreach](sponsors/cloudreach_logo.png "Cloudreach")](https://www.cloudreach.com)
