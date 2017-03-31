=======
Sceptre
=======


About
-----

Sceptre is a tool to drive AWS `CloudFormation <https://aws.amazon.com/cloudformation/>`_. It automates away some of the more mundane, repetitive and error-prone tasks, allowing you to concentrate on building better infrastructure.

Features:

- Code reusability by separating a stack's template and its configuration
- Support for templates written in JSON, YAML or Python DSLs such as Troposphere
- Dependency resolution by passing of stack outputs to parameters of dependent stacks
- Environment support by bundling related stacks into logical groups (e.g. dev and prod)
- Environment-level commands, such as creating multiple stacks with a single command
- Fast, highly parallelised builds
- Built in support for working with stacks in multiple AWS accounts
- Infrastructure visibility with meta-operations such as stack querying protection
- Support for inserting dynamic values in templates via customisable resolvers
- Support for running arbitrary code as hooks before/after stack builds


Example
-------

Sceptre organises stacks into environments. Each stack is represented by a YAML configuration file stored in a directory which represents the environment. Here, we have two stacks, ``vpc`` and ``subnets``, in an environment named ``dev``::

  $ tree
  .
  ├── config
  │   └── dev
  │       ├── config.yaml
  │       ├── subnets.yaml
  │       └── vpc.yaml
  └── templates
      ├── subnets.py
      └── vpc.py


We can create a stack with the ``create-stack`` command. This ``vpc`` stack contains a VPC::

  $ sceptre create-stack dev vpc
  dev/vpc - Creating stack
  dev/vpc VirtualPrivateCloud AWS::EC2::VPC CREATE_IN_PROGRESS
  dev/vpc VirtualPrivateCloud AWS::EC2::VPC CREATE_COMPLETE
  dev/vpc sceptre-demo-dev-vpc AWS::CloudFormation::Stack CREATE_COMPLETE


The ``subnets`` stack contains a subnet which must be created in the VPC. To do this, we need to pass the VPC ID, which is exposed as a stack output of the ``vpc`` stack, to a parameter of the ``subnets`` stack. Sceptre automatically resolves this dependency for us::

  $ sceptre create-stack dev subnets
  dev/subnets - Creating stack
  dev/subnets Subnet AWS::EC2::Subnet CREATE_IN_PROGRESS
  dev/subnets Subnet AWS::EC2::Subnet CREATE_COMPLETE
  dev/subnets sceptre-demo-dev-subnets AWS::CloudFormation::Stack CREATE_COMPLETE


Sceptre implements meta-operations, which allow us to find out information about our stacks::

  $ sceptre describe-env-resources dev
  dev/subnets:
  - LogicalResourceId: Subnet
    PhysicalResourceId: subnet-445e6e32
  dev/vpc:
  - LogicalResourceId: VirtualPrivateCloud
    PhysicalResourceId: vpc-c4715da0


Sceptre provides environment-level commands. This one deletes the whole ``dev`` environment. The subnet exists within the vpc, so it must be deleted first. Sceptre handles this automatically::

  $ sceptre delete-env dev
  dev/subnets - Deleting stack
  dev/subnets Subnet AWS::EC2::Subnet DELETE_IN_PROGRESS
  dev/subnets - Stack deleted
  dev/vpc - Deleting stack
  dev/vpc VirtualPrivateCloud AWS::EC2::VPC DELETE_IN_PROGRESS
  dev/vpc - Stack deleted


Usage
-----

Sceptre can be used from the CLI, or imported as a Python package.

CLI::

  Usage: sceptre [OPTIONS] COMMAND [ARGS]...

  Options:
  --version             Show the version and exit.
  --debug               Turn on debug logging.
  --dir TEXT            Specify sceptre directory.
  --output [yaml|json]  The formatting style for command output.
  --no-colour           Turn off output colouring.
  --var TEXT            A variable to template into config files.
  --var-file FILENAME   A YAML file of variables to template into config
                        files.
  --help                Show this message and exit.

  Commands:
  continue-update-rollback  Roll stack back to working state.
  create-change-set         Creates a change set.
  create-stack              Creates the stack.
  delete-change-set         Delete the change set.
  delete-env                Delete all stacks.
  delete-stack              Delete the stack.
  describe-change-set       Describe the change set.
  describe-env              Describe the stack statuses.
  describe-env-resources    Describe the env's resources.
  describe-stack-outputs    Describe stack outputs.
  describe-stack-resources  Describe the stack's resources.
  execute-change-set        Execute the change set.
  generate-template         Display the template used.
  get-stack-policy          Display the stack policy used.
  launch-env                Creates or updates all stacks.
  launch-stack              Create or launch the stack.
  list-change-sets          List change sets.
  lock-stack                Prevent stack updates.
  set-stack-policy          Set stack policy.
  unlock-stack              Allow stack updates.
  update-stack              Update the stack.
  update-stack-cs           Update the stack via change set.
  validate-template         Validate the template.


Python:

.. code-block:: python

  from sceptre.environment import Environment

  env = Environment("/path/to/sceptre_dir", "environment_name")
  stack = env.stacks["stack_name"]
  stack.create()

A full API description of the sceptre package can be found in the `Documentation <http://sceptre.cloudreach.com/docs/sceptre.html>`__.


Install
-------

::

  $ pip install sceptre

More information on installing sceptre can be found in our `Installation Guide <http://sceptre.cloudreach.com/docs/installation.html>`_.


Tutorial and Documentation
--------------------------

- `Get Started <http://sceptre.cloudreach.com/docs/get_started.html>`_
- `Documentation <http://sceptre.cloudreach.com/docs/>`__


Contributions
-------------

See our `Contributing Guide <CONTRIBUTING.rst>`_.
