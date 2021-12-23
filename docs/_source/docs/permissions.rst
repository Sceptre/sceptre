Sceptre and IAM
===============

Inevitably, when working with CloudFormation (or anything in AWS, really), IAM permissions are
relevant. **By default, Sceptre uses the permissions of the user executing Sceptre commands when
performing any of its actions.** Also, by default, CloudFormation uses the permissions of the user
executing its actions when performing any of the actions on individual resources that it performs.

This means that, by default, if the user executing Sceptre has admin-level permissions, there won't
be any issue executing any actions. But this is often not a viable option. Organizations usually have
few users with these permissions. Furthermore, there are legitimate reasons for not wanting to grant
users (or CI/CD systems) admin-level permissions.

Of course, admin-level AWS permissions aren't essential; At the end of the day, Sceptre and
CloudFormation actually only need the permissions necessary to perform the required actions for a
given project on the resources that will be managed by Sceptre/CloudFormation. The actual range of
permissions required tends to be a much narrower scope than admin-level. Using Sceptre can indeed
align with the "Principle of Least Privilege".

Permissions Configurations
--------------------------

There are two main configurations for Sceptre that can modify default permissions behavior to
provide more flexibility, control, and safety within an organization: **role_arn** and **iam_role**
These can be applied in a very targeted way, on a stack by stack basis or can be applied broadly to a
whole StackGroup.


role_arn
^^^^^^^^
This is the **CloudFormation service role** that will be attached to a given CloudFormation stack.
This IAM role needs to be able to be assumed by **CloudFormation**, and must provide all the
necessary permissions for all create/read/update/delete operations for all resources defined in that
stack. If CloudFormation can assume this role, the user executing Sceptre does not need those
permissions.

There are a few very important things to note about using a CloudFormation service role:

* You cannot remove a role from a stack once you've added it. You'd have to delete and rebuild the
  stack without it if you wanted to remove it. You *may*, however, replace one role with another on
  the stack.
* Once the role has been added to a stack, it will *always* be used for all actions; It doesn't matter
  who is executing them; those permission cannot be overridden.
* You cannot delete a stack with a service role unless that role has permissions to do so. This means
  that an admin might need to add deletion permissions to that role before that stack can be removed.

Applying a service role to a stack is a very effective way to grant (and limit) the scope of permissions
that a stack can utilize, but the rigidity of using it might prove overly burdensome, depending on
the use case.

For more information on using CloudFormation service roles, see the `AWS documentation <https://docs.aws
.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html>`_.

As a resolvable property, Sceptre allows you to use a resolver to populate the ``role_arn`` for a
Stack or StackGroup Config. This means you could define that role within your project, output its
ARN, and then reference it using `!stack_output`.


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
  permissions of the current user, but it interprets the current user to be the indicated ``iam_role``,
  which could grant additional permissions.

Using the ``iam_role`` configuration on a Stack or StackGroup Config allows the user to temporarily
"step into" a different set of permissions in order to execute Sceptre actions on Stack(s) in the
project without having to permanently grant those permissions to that user.

In order to use an ``iam_role`` on a Sceptre Stack Config, that role needs to have an
AssumeRolePolicyDocument that allows the current user to assume it.

As a resolvable property, Sceptre allows you to use a resolver to populate the ``iam_role`` for a
Stack or StackGroup Config. This means you could define that role within your project, output its
ARN, and then reference it using `!stack_output`.

Configuring CI/CD Systems without Admin access
----------------------------------------------

One of the most useful ways to employ Sceptre is via an automated deployment pipeline powered by a
tool like Jenkins or CircleCI. However, there are often organizational policies against giving such
systems admin-level access to an AWS account. Sceptre *can* operate under these sorts of policies
(with some careful planning).

While requirements differ from use case to use case, the following might be a viable strategy could
work for your organization. It can be entirely implemented using Sceptre.

* **The permissions boundary**: Your organization defines a managed policy to use as a `permissions boundary
  <https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html>`_ that defines the
  maximum range of permissions that could possibly be assumed by a "deployment role" (see below).

  * A permissions boundary can require that any IAM roles created also possess a given permissions
    boundary, so if your project needs to create other IAM roles, the boundary could constrain the
    scope of permissions those other roles could create. If this is the case, you might want to create
    two separate permissions boundaries; One of the deployment role and one for roles created by the
    deployment role.
  * **Remember: A permissions boundary doesn't actually *grant* any permissions; it only defines the
    maximum range of permissions that *could* be granted.** You can use it to protect your
    "untouchable" resources that you don't want the CI/CD system to affect.
  * You should set the path on the permissions boundary to a special namespace,
    like "deployment" and the expressly prohibit any role with this permissions boundary from taking
    any create/update/delete action on any IAM resources on that path. This will prevent the CI/CD
    system from being able to escalate or alter its own permissions.
* **The deployment role**: This is the role that will be **assumed** (not possessed) by the CI/CD
  system, empowering it to deploy your Sceptre project.

  * It must have an AssumeRolePolicyDocument that *only* permits the user/role of the CI/CD system
    to assume it. Thus you can prevent anyone else in the organization from assuming it.
  * This role should have all the permissions Sceptre requires to perform its deployments on all the
    sorts of resources it needs. So long as the permissions boundary guards against unwanted actions,
    permissions on the deployment role can be rather broad since it will be constrained by the
    permissions boundary.
  * You should set the path on the deployment role to the same path as the permissions boundary.
* **Set the ``iam_role``** on all Sceptre Stacks *that are not the permissions boundary or deployment
  role* as the ARN of the `deployment_role`. This means that the CI/CD system will be instructed to
  step into the deployment role to execute the actions on all stacks except the deployment role or
  permissions boundary stack.
* **Have an AWS Admin user *manually* deploy** the permissions boundary and deployment role with
  Sceptre.
* **The CI/CD system will be able to assume the deployment role** to launch the rest of your project
  safely within the bounds of that role, but will not be able to deploy any changes to that role or
  its permissions boundary.

Example
^^^^^^^

.. code-block:: yaml

    AWSTemplateFormatVersion: "2010-09-09"

    Parameters:
        DeployerArn:
            Type: String
            Description: The ARN of the IAM user/role to allow the role to be assumed by
        CreatedResourcesPath:
            Type: String
            Description: >-
                The Path that the Deployment Role will need to create IAM resources on. This is
                effectively the namespace that all IAM resources created by the CI/CD will be under.
                This will prevent naming conflicts as well as prevent the CI/CD system from being
                able to operate on OTHER resources not in this namespace. This path cannot be
                "deployment" and cannot include slashes.
            AllowedPattern: '(?!deployment)[a-z_]*'

    Resources:
        # This is the permissions boundary that MUST be on all roles CREATED BY the Deployment
        # Role. In other words, the Deployment Role can only create roles that have fewer
        # permissions than itself. As a permissions boundary, this provides the maximum set
        # of permissions that can possibly be added to a given role created by the Deployment
        # Role. It currently does not allow any create/update IAM permissions and has some explicit
        CreatedRolePermissionsBoundary:
            Type: AWS::IAM::ManagedPolicy
            Properties:
                Description: The permissions boundary that MUST be on all roles created by deployment roles
                # This is on the DEPLOYMENT path, not the created resources path, so it cannot be
                # tinkered with by the CI/CD system
                Path: /deployment/
                PolicyDocument:
                    Version: "2012-10-17"
                    Statement:
                        # Because this is a permissions boundary, we don't want to unnecessarily exclude
                        # any actions. Remember: Permissions boundaries don't GRANT permissions, they
                        # only define the full range of permissions that CAN be granted by a given role's
                        # policies. In this case, we'll allow anything NOT related to iam.
                        -   Sid: AllowNonIAMActions
                            Effect: Allow
                            NotAction: "iam:*"
                            Resource: "*"
                        # This statement allows created roles Read-only permissions on IAM resources
                        -   Sid: AllowIAMReadActions
                            Effect: Allow
                            Resource: "*"
                            Action:
                                - iam:Get*
                                - iam:List*
                        # This is an explicit denial on any actions performed on resources tagged
                        # with the "Environment" tag and the value of "Protected". So long
                        # as you have been diligent with tagging, this will work just fine. But you
                        # can deny any number of things you want to protect. This is just an example
                        -   Sid: DenyProtectedActions
                            Effect: Deny
                            Action: "*"
                            Resource: "*"
                            Condition:
                                StringLike
                                    aws:ResourceTag/Environment:
                                        - Protected

        # This role will be assumed by the CI/CD system temporarily in order to deploy the CloudFormation
        # changes. As a permissions boundary, this does not actually GRANT the role any permissions,
        # but rather defines the maximum range of permissions that can be granted to that role.
        DeploymentRolePermissionsBoundary:
            Type: AWS::IAM::ManagedPolicy
            Properties:
                Description: The Permissions Boundary to be used for deployment.
                # This is on the DEPLOYMENT path, not the created resources path, so it cannot be
                # tinkered with by the CI/CD system.
                Path: /deployment/
                PolicyDocument:
                    Version: "2012-10-17"
                    Statement:
                        # This statement ALLOWS the DeploymentRole to create roles and attach policies
                        # to roles, but ONLY roles that (1) are namespaced with the CreatedResources path
                        # and (2) have the CreatedRolePermissionsBoundary on them.
                        -   Sid: IAMRoleUpdationActions
                            Effect: Allow
                            Action:
                                - iam:CreateRole
                                - iam:PutRolePolicy
                                - iam:UpdateRole
                                - iam:UpdateRoleDescription
                                - iam:DeleteRolePolicy
                                - iam:AttachRolePolicy
                                - iam:DetachRolePolicy
                                - iam:PutRolePermissionsBoundary
                            # These operations are only allowed on the created resources path, NOT on
                            # the deployment path, which means the Deployment Role cannot expand its own
                            # permissions. It's also relevant to note that this assumes the created role
                            # is TAGGED with the CreatedResourcesPath tag, which must have a valid value
                            # in order to be allowed to utilize these permissions.
                            Resource: !Sub "arn:aws:iam::${AWS::AccountId}:role/${!aws:PrincipalTag/CreatedResourcesPath}/*"
                            Condition:
                                # This condition is SUPER important. It means that the only roles that can
                                # be created or updated with policies are those that have the permissions
                                # boundary listed above.
                                StringEquals:
                                    "iam:PermissionsBoundary": !Ref CreatedRolePermissionsBoundary
                                # This means that the only way that any of these actions can be allowed
                                # are if CloudFormation is directly invoking these. The Deployer cannot
                                # execute these actions directly, even if they've assumed the right role
                                # with the right permissions.
                                "ForAnyValue:StringEquals":
                                    "aws:CalledVia": [ 'cloudformation.amazonaws.com' ]
                        # This controls other IAM actions and ensures that they can ONLY be enacted upon
                        # roles that are on the CreatedResourcesPath, NOT the Deployment path.
                        -   Sid: IamRoleActions
                            Effect: Allow
                            Action:
                                - iam:DeleteRole
                                - iam:DeleteServiceLinkedRole
                                - iam:PassRole
                                - iam:TagRole
                                - iam:UntagRole
                            # These actions are only allowed within the configured CreatedResourcesPath,
                            # as indicated by that tag on the deploying role.
                            Resource: !Sub "arn:aws:iam::${AWS::AccountId}:role/${!aws:PrincipalTag/CreatedResourcesPath}/*"
                            Condition:
                                # These actions cannot happen unless they were directly invoked by
                                # CloudFormation. A deployer cannot trigger these actions directly.
                                "ForAnyValue:StringEquals":
                                    "aws:CalledVia": [ 'cloudformation.amazonaws.com' ]
                        # Similarly, The only policies that can be managed are those namespaced by the
                        # CreatedResourcesPath. The Deployment role cannot mess with other roles.
                        -   Sid: IAMPolicyUpdateActions
                            Effect: Allow
                            Action:
                                - iam:CreatePolicy
                                - iam:CreatePolicyVersion
                                - iam:DeletePolicy
                                - iam:DeletePolicyVersion
                                - iam:TagPolicy
                                - iam:UntagPolicy
                            # These actions are only allowed within the configured CreatedResourcesPath,
                            # as indicated by that tag on the deploying role.
                            Resource: !Sub "arn:aws:iam::${AWS::AccountId}:policy/${!aws:PrincipalTag/CreatedResourcesPath}/*"
                            Condition:
                                "ForAnyValue:StringEquals":
                                    "aws:CalledVia": [ 'cloudformation.amazonaws.com' ]
                        # We will allow all read operations for the Deployment role on all resources.
                        # This shouldn't actually involve any real risk, since it is read-only.
                        -   Sid: AllowIAMReadAccess
                            Effect: Allow
                            Action:
                                - iam:Get*
                                - iam:List*
                            Resource: "*"
                        # In order to restrict operations that are done to only those originating with
                        # CloudFormation, we then need to allow operations on CloudFormation directly
                        # from this permissions boundary.
                        -   Sid: AllowCloudFormationActions
                            Effect: Allow
                            Action: "cloudformation:*"
                            Resource: "*"
                        # All other actions are allowed in this permissions boundary except IAM actions
                        # that haven't already been allowed for elsewhere within this boundary. In other
                        # words, you couldn't set up a new SAML provider or create an IAM user, but you
                        # CAN create an IAM Role (under certain circumstances), since that permission is
                        # allowed above. Remember: Permissions boundaries don't GRANT permissions, they
                        # only define the maximum range of permissions that CAN be granted.
                        -   Sid: AllowEverythingElseButIAMFromCloudFormation
                            Effect: Allow
                            # Meaning everything EXCEPT iam operations not otherwise accounted for or
                            # denied.
                            NotAction: "iam:*"
                            Resource: "*"
                            Condition:
                                # While we might allow the POSSIBILITY of broad permissions not otherwise
                                # accounted for or denied, we only want to allow those permissions to be
                                # executed via CloudFormation (or at least set off by CloudFormation).
                                # By using CalledViaFirst, we allow the possibility of a passed role from
                                # CloudFormation to some other service to execute actions, but
                                # CloudFormation must ultimately be responsible for that execution.
                                "ForAnyValue:StringEquals":
                                    "aws:CalledViaFirst": [ 'cloudformation.amazonaws.com' ]
                        # Some operations need to precede CloudFormation operations, such as putting a
                        # cloudformation template or other sort of artifact onto S3 prior to triggering
                        # deployment via CloudFormation.
                        -   Sid: AllowS3PutObjectToPutTemplates
                            Effect: Allow
                            Resource: "*"
                            Action:
                                - "s3:PutObject"
                                - "s3:GetBucketLocation"
                                - "s3:ListBucket"
                        # This is an explicit denial on any actions performed on resources tagged
                        # with the "Environment" tag and the value of "Protected". You
                        # can deny any number of things you want to protect. This is just an example
                        -   Sid: DenyProtectedActions
                            Effect: Deny
                            Action: "*"
                            Resource: "*"
                            Condition:
                                StringLike
                                    aws:ResourceTag/Environment:
                                        - Protected

        # This is the role that will be ASSUMED by the CI/CD system in order to deploy the all cloudformation
        # resources for this project, including any IAM-based resources. It will be constrained by the
        # DeploymentRolePermissionsBoundary, which will limit the scope of its permissions.
        DeploymentRole:
            Type: AWS::IAM::Role
            Properties:
                Description: >-
                    This is the role Jenkins will use in order to deploy changes using Sceptre. It
                    has broad permissions, but it's important to note that it also has a defined
                    permissions boundary that limits the range and scope of those permissions. This
                    role DOES have the ability to effect IAM changes, but only those within the right
                    path and explicitly allowed for within the permissions boundary.
                # We use a permissions boundary to define the maximum range of permissions that could
                # possibly be assumed by this role. This makes it safer to provide more generic permissions
                # on this role, like "PowerUserAccess".
                PermissionsBoundary: !Ref DeploymentRolePermissionsBoundary
                AssumeRolePolicyDocument:
                    Version: "2012-10-17"
                    Statement:
                        -   Effect: "Allow"
                            Principal:
                                # This role can ONLY be assumed by the configured deployer, which
                                # should be your CI/CD system's role.
                                AWS:
                                    - !Ref DeployerArn
                            Action: "sts:AssumeRole"
                # Because this is on the DEPLOYMENT path, not the created resources path, this role is
                # unable to alter itself, due to the permissions boundary on it.
                Path: !Sub "/deployment/${CreatedResourcesPath}/"
                ManagedPolicyArns:
                    # These permissions are pretty broad, but remember, they cannot go beyond the
                    # defined permissions boundary, so they are always going to be constrained by that.
                    # PowerUserAccess has the ability to update MOST things, but has no IAM permissions
                    - "arn:aws:iam::aws:policy/PowerUserAccess"
                    - "arn:aws:iam::aws:policy/IAMReadOnlyAccess"
                Tags:
                    # This tag is required by the permissions boundary to ensure that this role can only
                    # operate on resources on that path.
                    -   Key: "CreatedResourcesPath"
                        Value: !Ref CreatedResourcesPath

        # This is a special inline policy we'll add to the managed policies above. It lets the deployment
        # role perform the required IAM operations within the created resources path. Remember, the
        # permissions boundary set on the deployment role will constrain these permissions further.
        IamCreationPolicy:
            Type: AWS::IAM::Policy
            Properties:
                PolicyName: IAMCreationPolicy
                Roles:
                    - !Ref DeploymentRole
                PolicyDocument:
                    Version: "2012-10-17"
                    Statement:
                        # This statement allows IAM role Create/update/delete permissions for the
                        # Deployment role, but only on those roles that are namespaced with the Created
                        # Resources path. Note: The role's permission boundary will constrain these
                        # Permissions further.
                        -   Sid: AllowIAMRoleActions
                            Effect: Allow
                            Action:
                                - iam:CreateRole
                                - iam:CreateServiceLinkedRole
                                - iam:PutRolePolicy
                                - iam:UpdateRole
                                - iam:UpdateRoleDescription
                                - iam:DeleteRole
                                - iam:DeleteServiceLinkedRole
                                - iam:DeleteRolePolicy
                                - iam:AttachRolePolicy
                                - iam:DetachRolePolicy
                                - iam:TagRole
                                - iam:UntagRole
                                - iam:PutRolePermissionsBoundary
                                - iam:PassRole
                            Resource: !Sub "arn:aws:iam::${AWS::AccountId}:role/${CreatedResourcesPath}/*"
                        # This statement allows for IAM Policy create/update/delete permissions for the
                        # Deployment role, but only those policies that are namespaced with the Created
                        # Resources path. Note: The permissions boundary on the role will constraint these
                        # permissions further.
                        -   Sid: IAMPolicyActions
                            Effect: Allow
                            Action:
                                - iam:CreatePolicy
                                - iam:CreatePolicyVersion
                                - iam:DeletePolicy
                                - iam:DeletePolicyVersion
                                - iam:TagPolicy
                                - iam:UntagPolicy
                            Resource: !Sub "arn:aws:iam::${AWS::AccountId}:policy/${CreatedResourcesPath}/*"



Basic permissions that Sceptre requires
---------------------------------------

There are certain permissions that Sceptre requires to perform even its most basic operations. These
include:

Basic operations:

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

If using change sets:

* cloudformation:CreateChangeSet
* cloudformation:DeleteChangeSet
* cloudformation:DescribeChangeSet
* cloudformation:ExecuteChangeSet
* cloudformation:ListChangeSets

If using a template bucket:

* s3:CreateBucket
* s3:PutObject

If using ``role_arn``:

* iam:PassRole

If using ``iam_role``:

* sts:AssumeRole
