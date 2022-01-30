Architecting Sceptre
====================

Sceptre is written in a way that aims to be unopinionated in how it is used. It
is designed to work equally well with simple and complex infrastructures.
Sceptre’s flexible nature, and the variation in how people organise their AWS
accounts, makes it difficult to give generic advice on how best to use it, as
it can be use-case specific. However, the following patterns have emerged from
our use of Sceptre at Cloudreach.

Project layout
--------------

Sceptre’s nested stack groups means that it is possible to store an entire
company or department’s infrastructure in a single Sceptre project. While this
is possible, it isn’t recommended. Having a large number of developers interact
with a single repository can be difficult from a version control point of view,
and it might be dangerous to let developers touch infrastructure that they are
not directly involved with.

We recommend different Sceptre projects for each large ‘section’ of the
infrastructure being built.

Directory layout
----------------

You need to store your :doc:`Sceptre templates <templates>` in the ``templates`` directory within
your Sceptre Project.

.. code-block:: text

   .
   ├── config
   └── templates

StackGroup structure
--------------------

StackGroups can be arbitrarily nested, and StackGroup commands can be applied
to any level of the StackGroup tree. This can make it difficult to know how to
divide StackGroups up.

When considering how to split StackGroups up, it’s useful to remember the
following properties of StackGroups:

1. Region specific. There is no way for an StackGroup to launch stacks in
   multiple regions; a StackGroup can, however, contain sub-StackGroups in
   different regions. A StackGroup should therefore contain Stacks that belong
   in the same region.

2. Command related. StackGroup level commands (like ``launch``) are applied to
   every stack in a StackGroup. There is no way to exclude stacks from an
   StackGroup level command. Therefore, StackGroups should contain stacks that
   can be launched and deleted together.

   Some stacks are inherently longer-lived than others. Stacks containing
   VPC-level infrastructure are likely to be longer lived than stacks
   containing an ephemeral testing environment. It therefore makes sense to
   split these up into separate StackGroups.

Example architectures
---------------------

The following examples demonstrate how we might architect various Sceptre
projects. Only configuration layout is shown, and the examples are merely meant
to demonstrate ways of organising different projects.

-  Application development within an externally defined VPC

    .. code-block:: text

        config/
            config.yaml
            prod/
                application/
                    asg.yaml
                    security-group.yaml
            database/
                rds.yaml
                security-group.yaml

-  DevOps team who manage all the infrastructure for their service

    .. code-block:: text

        config/
            config.yaml
            prod/
                network
                vpc.yaml
                subnet.yaml
            frontend/
                api-gateway.yaml
            application/
                lambda-get-item.yaml
                lambda-put-item.yaml
            database/
                dynamodb.yaml

-  Centralised, company-wide networking

    .. code-block:: text

        config/
            config.yaml
            prod/
                vpc.yaml
                public-subnet.yaml
                application-subnet.yaml
                database-subnet.yaml
            dev/
                vpc.yaml
                public-subnet.yaml
                application-subnet.yaml
                database-subnet.yaml

-  IAM management

    .. code-block:: text

        config/
            config.yaml
            account-1/
                iam-role-admin.yaml
                iam-role-developer.yaml
            account-2/
                iam-role-admin.yaml
                iam-role-developer.yaml

- Replicated environments with only config differences

    In this architecture, there is a var-file with each environment's configurations. Each var-file
    has the same keys, but values specific to that environment. The Stack configs and StackGroup
    configs reference keys from from those files. This way the environment could be tested in
    non-production environments, then deployed to production by simply referencing a different
    var-file.

    .. code-block:: text

        config/
            config.yaml
            project/
                vpc.yaml
                network.yaml
                database.yaml
        vars/
            production.yaml
            staging.yaml
            development.yaml

A complete Sceptre project example, explained
---------------------------------------------

This is a detailed example project setup for all infrastructure needs for a given application called
"Indigo." Here are a few basic assumptions of this example:

* Indigo's infrastructure will be deployed automatically using a CI/CD system (such as Jenkins).
* The AWS role held by the CI/CD system cannot have sweeping, admin-level IAM permissions. It is
  used by other teams in the company and cannot have its permissions modified for the Indigo
  project.
* Not all infrastructure in the organization is deployed/maintained by Sceptre and Indigo will need
  to interact with that infrastructure.
* All infrastructure for Indigo should be managed by Sceptre, including any required deployment
  resources.
* Developers will need to be able to stand up their own, isolated environments of Indigo that do not
  conflict with production. These environments will have some different configurations to make them
  cheaper for the company, but otherwise be identical to production.

Project Structure
*****************

.. code-block:: text

    config/
        config.yaml             # top-level project configuration
        indigo/                 # StackGroup for all Indigo's resources
            config.yaml         # StackGroup Config for Indigo
            application.yaml    # Stack Config for Indigo's application stack
        project/                # StackGroup for resources needed to deploy Indigo
            deployment.yaml     # Stack Config for Indigo's deployment resources
    templates/
        indigo/
            application.yaml
        project/
            deployment.yaml
    vars/
        production.yaml         # var-file with the production environment's configurations
        development.yaml        # var-file with configurations for development environments

Example Configs
***************

Top-level project configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

    # config/config.yaml

    # This is the top-level config file for the whole project. Every stack in the project will
    # inherit these settings unless they explicitly override them. At minimum, you need the
    # project_code and region, but you can set whatever StackGroup and Stack configurations you
    # want inherited by the rest of the project.

    # By making the project-code parameterized by environment name, it guarantees that one
    # environment's stacks do not conflict with another environment's stacks.
    project_code: indigo-{{ var.environment }}
    region: {{ var.region }}

    # Setting the template_bucket_name with a !stack_output means that every stack in the project
    # (except the deployment stack) will have its template uploaded to that bucket. It ALSO means
    # that every stack in the project will inherit a dependency on the deployment stack (except the
    # deployment stack... see its comments below)
    template_bucket_name: !stack_output project/deployment.yaml::BucketName

    # By making the template_key_prefix parameterized by environment, it means that every
    # environment's templates will be uploaded to its own directory structure within the template
    # bucket, preventing conflicts.
    template_key_prefix: {{ var.environment }}

    # Setting the iam_role on the project like this means that all Sceptre actions on all stacks in
    # the project will be done by assuming the deployment role whose ARN is output by the deployment
    # stack (except for actions on the deployment stack... see its comments below).
    iam_role: !stack_output project/deployment.yaml::DeploymentRoleArn


The Deployment Stack
^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

    # config/project/deployment.yaml

    # This is a StackConfig for a stack that defines the project's basic requirements, that all
    # stacks and all environments will depend on for deployment to work. Because the project config
    # references this stack using !stack_output, all OTHER stacks in the project will depend upon
    # this one.

    # We override the project_code here so that there will only be ONE stack for deployment that is
    # shared across all environments.
    project_code: indigo-deployment

    # Setting is_project_dependency has a few important effects for this stack
    #   1. It disables dependencies. In other words, this stack cannot depend on any other stack.
    #       This is how it bypasses the circular dependency that it would otherwise inherit from
    #       the project's config (config/config.yaml)
    #   2. It disables the !stack_output resolver, making it resolve to nothing. In other words, it
    #       cannot inherit the template_bucket_name or iam_role from the project config. This is
    #       good because this stack DEFINES the template bucket and iam_role.
    is_project_dependency: True

    # This template defines an S3 Bucket, outputting the created bucket as "BucketName" and an IAM
    # role that can be assumed by the CI/CD system's role/user, outputting the ARN as
    # "DeploymentRoleArn". This "Deployment role" will need permissions to execute actions on
    # CloudFormation as well as any perform any actions required by the stack's permissions.
    template:
        path: project/deployment.yaml

The StackGroup Config
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

    # config/indigo/config.yaml

    # This is the StackGroup config for the indigo StackGroup. Any settings set here will be shared
    # by all stacks in it.

    # By defining tags at the StackGroup level, all stacks will inherit those tags and
    # CloudFormation will then propagate those tags to all resources within those stacks that
    # support tags.
    stack_tags:
        Environment: {{ var.environment }}
        DeployedVia: Sceptre

The Application Stack Config
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

    # config/indigo/application.yaml

    # This is the Stack config for the application stack. It inherits all configurations from all
    # StackGroup configs for StackGroups in which it resides (in this case, the
    # config/indigo/config.yaml and config/config.yaml). These inherited configurations include the
    # inherited template_bucket_name and iam_role configurations and their dependency on the
    # deployment stack.

    template:
        path: indigo/application.yaml

    parameters:
        # It's good practice to namespace all resources that you apply a name to in your stacks. Doing
        # so with an environment name is very useful to avoid name collisions.
        EnvironmentName: {{ var.environment }}
        VpcId: {{ var.indigo.vpc.vpc_id }}
        InstanceType: {{ var.indigo.rds.instance_type }}

Per-Environment Var-Files
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

    # vars/production.yaml

    # This var-file contains the configurations for the "production" environment. Every {{ var }}
    # reference in stack configs or stack group configs must be supplied when using sceptre, either
    # via var-files (using the `--var-file` argument) or by explicitly passing them
    # (using the `--var` argument). This var-file contains every variable referenced in all the
    # configs.

    environment: production
    region: us-west-2

    indigo:
        vpc:
            vpc_id: "vpc-abc1234"  # Production vpc
        rds:
            # Production uses a very large instance
            instance_type: "db.m5.8xlarge"

.. code-block:: yaml

    # vars/development.yaml

    # This var-file DOESN'T have the environment variable name specified, requiring the user of this
    # var-file to specify the environment name. This allows for easily launching isolated,
    # development environments for testing purposes. The environment name can be supplied when
    # performing stack actions like:
    #   sceptre --var-file vars/development.yaml --var environment=dev-johnny launch indigo

    region: us-west-2

    indigo:
        vpc:
            vpc_id: "vpc-def5678"  # Dev VPC
        rds:
            # Dev uses very small instances
            instance_type: "db.t2.small"

CI/CD Pipeline
^^^^^^^^^^^^^^

No matter the service you intend to use for deployment (whether it's Jenkins, CircleCI, or some
other), the flow for deployment likely will look the same.

Before you deploy, however, you need to have an admin user launch your deployment stack manually
using Sceptre. This stack is the stack that provides the permissions for your pipeline to execute
changes on the other stacks in the project.

Once launched, the CI/CD pipeline can launch the "indigo" StackGroup when it runs using
``sceptre --var-file vars/production.yaml launch indigo``.

Depending on requirements for your application or company policies, you might want to generate a
document for review prior to launching using the `sceptre diff` command, which will indicate all
changes are currently present in the files from what has been deployed.
