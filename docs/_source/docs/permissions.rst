Sceptre and IAM
===============

Inevitably, when working with CloudFormation, IAM permissions are relevant. **By default, Sceptre
uses the permissions of the user executing Sceptre commands when performing any of its actions.**
Also, by default, CloudFormation uses the permissions of the user executing its actions when
performing actions on individual resources within those stacks.

This means that, by default, if the user executing Sceptre has admin-level permissions, there won't
be any issue executing any actions. But this is often not a viable option. Organizations usually have
few users with these permissions. Furthermore, there are legitimate reasons for not wanting to grant
users (or CI/CD systems like Jenkins) admin-level permissions.

Of course, admin-level AWS permissions aren't essential; At the end of the day, Sceptre and
CloudFormation actually only need the permissions necessary to perform the required actions for a
given project on the resources that will be managed by them. The actual range of permissions required
tends to be a much narrower scope than admin-level.

Permissions Configurations
--------------------------

There are three main configurations for Sceptre that can modify default permissions behavior to
provide more flexibility, control, and safety within an organization: **role_arn**, **iam_role**, and
**profile**. These can be applied in a very targeted way, on a stack by stack basis or can be applied
broadly to a whole StackGroup.

.. _role_arn_permissions:

role_arn
^^^^^^^^
This is the **CloudFormation service role** that will be attached to a given CloudFormation stack.
This IAM role needs to be able to be assumed by **CloudFormation**, and must provide all the
necessary permissions for all create/read/update/delete operations for all resources defined in that
stack. If CloudFormation can assume this role, the user executing Sceptre does not need those
permissions, only ``iam:PassRole`` permissions on that role to give it to CloudFormation.

There are a few very important things to note about using a CloudFormation service role:

* You cannot remove a role from a stack once you've added it. You'd have to delete and rebuild the
  stack without it if you wanted to remove it. You *may*, however, replace one role with another on
  the stack.
* Once the role has been added to a stack, it will *always* be used for all actions; It doesn't matter
  who is executing them; those permission cannot be overridden without modifying the role itself or
  replacing it with another role.
* You cannot delete a stack with a service role unless that role has permissions to delete those
  resources. This means that an admin might need to add deletion permissions to that role before that
  stack can be removed.

Applying a service role to a stack is a very effective way to grant (and limit) the scope of permissions
that a stack can utilize, but the rigidity of using it might prove overly burdensome, depending on
the use case.

For more information on using CloudFormation service roles, see the `AWS documentation <https://docs.aws
.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html>`_.

As a resolvable property, Sceptre allows you to use a resolver to populate the ``role_arn`` for a
Stack or StackGroup Config. This means you could define that role within your project, output its
ARN, and then reference it using `!stack_output`.

.. _iam_role_permissions:

iam_role
^^^^^^^^

This is a **role that Sceptre will assume** when taking any actions on the Stack. It is not a service
role for CloudFormation. Instead, this is simply a role that the current user assumes to execute
any Sceptre actions on that stack. This has some benefits over a CloudFormation service role:

* This is not permanently attached to the Stack after you've used it once. If you ever *don't* want
  to assume this role, you could comment it out or remove it from the Stack Config and Sceptre simply
  won't use it. This is useful if the user executing Sceptre already has the right permissions to
  take those actions. In other words, it doesn't lock you in (unlike using ``role_arn``).
* CloudFormation can continue to use it's default behavior of executing Stack actions with the
  permissions of the current user, but it interprets the current user to hold the indicated ``iam_role``,
  which could grant additional permissions.

Using the ``iam_role`` configuration on a Stack or StackGroup Config allows the user to *temporarily*
"step into" a different set of permissions in order to execute Sceptre actions on Stack(s) in the
project without having to permanently hold those permissions.

In order to use an ``iam_role`` on a Sceptre Stack Config, that role needs to have an
AssumeRolePolicyDocument that allows the current user to assume it and permissions to perform all
deployment actions on the stack and all its resources.

As a resolvable property, Sceptre allows you to use a resolver to populate the ``iam_role`` for a
Stack or StackGroup Config. This means you could define that role within your project, output its
ARN, and then reference it using `!stack_output`.

.. _profile_permissions:

profile
^^^^^^^

This is different from ``role_arn`` and ``iam_role``, as both of those cause CloudFormation or
Sceptre to *assume* a different role with different permissions than the permissions the current
user has.

In contrast, the ``profile`` is simply an instruction for the underlying AWS SDK to reference that
profile in the user's local AWS configuration. It indicates which set of *credentials* to use when
operating on a given Stack or StackGroup. There is no call to AWS STS to assume a role temporarily.

Utilizing the ``profile`` configuration is identical to setting the ``AWS_PROFILE`` environment
variable, which has the same effect.

Tips for working with Sceptre, IAM, and a CI/CD system
------------------------------------------------------

* Rather than giving your CI/CD system blanket, admin-level permissions, you can define an IAM role
  with Sceptre to use for deploying the rest of your infrastructure, outputing its ARN in the template.
  Then, in the rest of your project's stacks, you can set the ``iam_role`` using ``!stack_output``
  to get that role's arn. This will mean your CI/CD system will temporarily "step into" that role
  when using Sceptre to interact with those specific stacks. It will also establish a dependency on
  your deployment role stack with every other stack in your project.

* You can constrain the permissions of that deployment role by using:

  * An ``AssumeRolePolicyDocument`` that only allows the CI/CD system to assume it (instead of just
    anyone in your organization).
  * A ``PermissionsBoundary`` that guards sensitive/critical infrastructure and which must be on
    any roles created/updated by the deployment role. See `AWS documentation on permission boundaries
    <https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html>`_ for more
    information.
  * The ``Path`` on IAM roles and managed policies to namespace your resources. Since that path is
    a part of the ARN structure on roles and managed policies, you can constrain the IAM-related
    permissions of the deployment role to only certain paths, preventing the deployment role from
    elevating its own permissions or modifying unrelated roles and policies.
  * Using ``aws:CalledVia`` and ``aws:CalledViaFirst`` conditions matching against
    ``"cloudformation.amazonaws.com"`` to ensure that the deployment role can only execute changes
    via CloudFormation and not on its own. Note: Some actions are taken by Sceptre directly and not
    via cloudformation (see the section below on this). Those actions should *not* have a CalledVia
    condition applied.

* If you define your deployment role (and any other related resources) using Sceptre and then
  reference it on all *other* stacks using ``iam_role: !stack_output ...``, this means that your
  CI/CD system will not be able to deploy changes to the deployment role or its resources, but that
  every deployment will depend on those. This is good! It means that, so long as those resources
  remain unchanged, automated deployment can proceed without issue. It also means that the scope of
  powers held by the deployment role needs to be reviewed by and **manually deployed by a user with
  admin-level permissions.** But after that manual deployment, your CI/CD system should be empowered
  to deploy all the other stacks in your project (so long as the deployment role has the full scope of
  permissions needed to do those deployments).

Basic permissions that Sceptre requires
---------------------------------------

There are certain permissions that Sceptre requires to perform even its most basic operations. These
include:

**For Basic operations:**

* cloudformation:CreateStack
* cloudformation:DeleteStack
* cloudformation:DescribeStackEvents
* cloudformation:DescribeStackResource
* cloudformation:DescribeStackResources
* cloudformation:DescribeStacks
* cloudformation:GetStackPolicy
* cloudformation:GetTemplate
* cloudformation:GetTemplateSummary
* cloudformation:ListStackResources
* cloudformation:ListStacks
* cloudformation:SetStackPolicy
* cloudformation:TagResource
* cloudformation:UntagResource
* cloudformation:UpdateStack
* cloudformation:UpdateTerminationProtection
* cloudformation:ValidateTemplate

**If using change sets:**

* cloudformation:CreateChangeSet
* cloudformation:DeleteChangeSet
* cloudformation:DescribeChangeSet
* cloudformation:ExecuteChangeSet
* cloudformation:ListChangeSets

**If using a template bucket:**

* s3:CreateBucket
* s3:PutObject

**If using a cloudformation service role:**

* iam:PassRole
