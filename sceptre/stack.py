# -*- coding: utf-8 -*-

"""
sceptre.stack

This module implements a Stack class, which stores a Stack's data.

"""

import logging
from typing import List, Any

from sceptre.connection_manager import ConnectionManager
from sceptre.exceptions import InvalidConfigFileError
from sceptre.helpers import get_external_stack_name, sceptreise_path
from sceptre.hooks import Hook, HookProperty
from sceptre.resolvers import (
    ResolvableContainerProperty,
    ResolvableValueProperty,
    RecursiveResolve,
    PlaceholderType,
)
from sceptre.template import Template


class Stack(object):
    """
    Stack stores information about a particular CloudFormation Stack.

    :param name: The name of the Stack.

    :param project_code: A code which is prepended to the Stack names\
            of all Stacks built by Sceptre.

    :param template_path: The relative path to the CloudFormation, Jinja2\
            or Python template to build the Stack from. If this is filled,
            `template_handler_config` should not be filled.

    :param template_handler_config: Configuration for a Template Handler that can resolve
            its arguments to a template string. Should contain the `type` property to specify
            the type of template handler to load. Conflicts with `template_path`.

    :param region: The AWS region to build Stacks in.

    :param template_bucket_name: The name of the S3 bucket the Template is uploaded to.

    :param template_key_prefix: A prefix to the key used to store templates uploaded to S3

    :param required_version: A PEP 440 compatible version specifier. If the Sceptre version does\
            not fall within the given version requirement it will abort.

    :param parameters: The keys must match up with the name of the parameter.\
            The value must be of the type as defined in the template.

    :param sceptre_user_data: Data passed into\
            `sceptre_handler(sceptre_user_data)` function in Python templates\
            or accessible under `sceptre_user_data` variable within Jinja2\
            templates.

    :param hooks: A list of arbitrary shell or python commands or scripts to\
            run.

    :param s3_details:

    :param dependencies: The relative path to the Stack, including the file\
            extension of the Stack.

    :param role_arn: The ARN of a CloudFormation Service Role that is assumed\
            by CloudFormation to create, update or delete resources.

    :param protected: Stack protection against execution.

    :param tags: CloudFormation Tags to be applied to the Stack.

    :param external_name:

    :param notifications: SNS topic ARNs to publish Stack related events to.\
            A maximum of 5 ARNs can be specified per Stack.

    :param on_failure: This parameter describes the action taken by\
            CloudFormation when a Stack fails to create.

    :param disable_rollback: If True, cloudformation will not rollback on deployment failures

    :param iam_role: The ARN of a role for Sceptre to assume before interacting\
            with the environment. If not supplied, Sceptre uses the user's AWS CLI\
            credentials.

    :param profile: The name of the profile as defined in ~/.aws/config and\
            ~/.aws/credentials.

    :param stack_timeout: A timeout in minutes before considering the Stack\
            deployment as failed. After the specified timeout, the Stack will\
            be rolled back. Specifying zero, as well as omitting the field,\
            will result in no timeout. Supports only positive integer value.

    :param ignore: If True, this stack will be ignored during launches (but it can be explicitly
            deployed with create, update, and delete commands.

    :param obsolete: If True, this stack will operate the same as if ignore was set, but it will
            also be deleted if the prune command is invoked or the --prune option is used with the
            launch command.

    :param iam_role_session_duration: The session duration when Scetre assumes a role.\
           If not supplied, Sceptre uses default value (3600 seconds)

    :param stack_group_config: The StackGroup config for the Stack

    """

    parameters = ResolvableContainerProperty("parameters")
    sceptre_user_data = ResolvableContainerProperty(
        "sceptre_user_data", PlaceholderType.alphanum
    )
    notifications = ResolvableContainerProperty("notifications")
    tags = ResolvableContainerProperty("tags")
    # placeholder_override=None here means that if the template_bucket_name is a resolver,
    # placeholders have been enabled, and that stack hasn't been deployed yet, commands that would
    # otherwise attempt to upload the template (like validate) won't actually use the template bucket
    # and will act as if there was no template bucket set.
    s3_details = ResolvableContainerProperty("s3_details", PlaceholderType.none)
    template_handler_config = ResolvableContainerProperty(
        "template_handler_config", PlaceholderType.alphanum
    )

    template_bucket_name = ResolvableValueProperty(
        "template_bucket_name", PlaceholderType.none
    )
    # Similarly, the placeholder_override=None for iam_role means that actions that would otherwise
    # use the iam_role will act as if there was no iam role when the iam_role stack has not been
    # deployed for commands that allow placeholders (like validate).
    iam_role = ResolvableValueProperty("iam_role", PlaceholderType.none)
    role_arn = ResolvableValueProperty("role_arn")

    hooks = HookProperty("hooks")

    def __init__(
        self,
        name: str,
        project_code: str,
        region: str,
        template_path: str = None,
        template_handler_config: dict = None,
        template_bucket_name: str = None,
        template_key_prefix: str = None,
        required_version: str = None,
        parameters: dict = None,
        sceptre_user_data: dict = None,
        hooks: Hook = None,
        s3_details: dict = None,
        iam_role: str = None,
        dependencies: List["Stack"] = None,
        role_arn: str = None,
        protected: bool = False,
        tags: dict = None,
        external_name: str = None,
        notifications: List[str] = None,
        on_failure: str = None,
        disable_rollback=False,
        profile: str = None,
        stack_timeout: int = 0,
        iam_role_session_duration: int = 0,
        ignore=False,
        obsolete=False,
        stack_group_config: dict = {},
    ):
        self.logger = logging.getLogger(__name__)

        if template_path and template_handler_config:
            raise InvalidConfigFileError(
                "Both 'template_path' and 'template' are set, specify one or the other"
            )

        if not template_path and not template_handler_config:
            raise InvalidConfigFileError(
                "Neither 'template_path' nor 'template' is set"
            )

        self.name = sceptreise_path(name)
        self.project_code = project_code
        self.region = region
        self.required_version = required_version
        self.external_name = external_name or get_external_stack_name(
            self.project_code, self.name
        )
        self.template_path = template_path
        self.dependencies = dependencies or []
        self.protected = protected
        self.on_failure = on_failure
        self.disable_rollback = self._ensure_boolean(
            "disable_rollback", disable_rollback
        )
        self.stack_group_config = stack_group_config or {}
        self.stack_timeout = stack_timeout
        self.profile = profile
        self.template_key_prefix = template_key_prefix
        self.iam_role_session_duration = iam_role_session_duration
        self.ignore = self._ensure_boolean("ignore", ignore)
        self.obsolete = self._ensure_boolean("obsolete", obsolete)

        self._template = None
        self._connection_manager = None

        # Resolvers and hooks need to be assigned last
        self.s3_details = s3_details
        self.iam_role = iam_role
        self.tags = tags or {}
        self.role_arn = role_arn
        self.template_bucket_name = template_bucket_name
        self.template_handler_config = template_handler_config

        self.s3_details = s3_details
        self.parameters = parameters or {}
        self.sceptre_user_data = sceptre_user_data or {}
        self.notifications = notifications or []

        self.hooks = hooks or {}

    def _ensure_boolean(self, config_name: str, value: Any) -> bool:
        if not isinstance(value, bool):
            raise InvalidConfigFileError(
                f"{self.name}: Value for {config_name} must be a boolean, not a {type(value).__name__}"
            )
        return value

    def __repr__(self):
        return (
            "sceptre.stack.Stack("
            f"name='{self.name}', "
            f"project_code={self.project_code}, "
            f"template_path={self.template_path}, "
            f"template_handler_config={self.template_handler_config}, "
            f"region={self.region}, "
            f"template_bucket_name={self.template_bucket_name}, "
            f"template_key_prefix={self.template_key_prefix}, "
            f"required_version={self.required_version}, "
            f"iam_role={self.iam_role}, "
            f"iam_role_session_duration={self.iam_role_session_duration}, "
            f"profile={self.profile}, "
            f"sceptre_user_data={self.sceptre_user_data}, "
            f"parameters={self.parameters}, "
            f"hooks={self.hooks}, "
            f"s3_details={self.s3_details}, "
            f"dependencies={self.dependencies}, "
            f"role_arn={self.role_arn}, "
            f"protected={self.protected}, "
            f"tags={self.tags}, "
            f"external_name={self.external_name}, "
            f"notifications={self.notifications}, "
            f"on_failure={self.on_failure}, "
            f"disable_rollback={self.disable_rollback}, "
            f"stack_timeout={self.stack_timeout}, "
            f"stack_group_config={self.stack_group_config}, "
            f"ignore={self.ignore}, "
            f"obsolete={self.obsolete}"
            ")"
        )

    def __str__(self):
        return self.name

    def __eq__(self, stack):
        # We should not use any resolvable properties in __eq__, since it is used when adding the
        # Stack to a set, which is done very early in plan resolution. Trying to reference resolvers
        # before the plan is fully resolved can potentially blow up.
        return (
            self.name == stack.name
            and self.external_name == stack.external_name
            and self.project_code == stack.project_code
            and self.template_path == stack.template_path
            and self.region == stack.region
            and self.template_key_prefix == stack.template_key_prefix
            and self.required_version == stack.required_version
            and self.iam_role_session_duration == stack.iam_role_session_duration
            and self.profile == stack.profile
            and self.dependencies == stack.dependencies
            and self.protected == stack.protected
            and self.on_failure == stack.on_failure
            and self.disable_rollback == stack.disable_rollback
            and self.stack_timeout == stack.stack_timeout
            and self.ignore == stack.ignore
            and self.obsolete == stack.obsolete
        )

    def __hash__(self):
        return hash(str(self))

    @property
    def connection_manager(self) -> ConnectionManager:
        """Returns the ConnectionManager for the stack, creating it if it has not yet been created.

        :returns: ConnectionManager.
        """
        if self._connection_manager is None:
            cache_connection_manager = True
            try:
                iam_role = self.iam_role
            except RecursiveResolve:
                # This would be the case when iam_role is set with a resolver (especially stack_output)
                # that uses the stack's connection manager. This creates a temporary condition where
                # you need the iam role to get the iam role. To get around this, it will temporarily
                # use None as the iam_role but will re-attempt to resolve the value in future accesses.
                # Since the Stack Output resolver (the most likely culprit) uses the target stack's
                # iam_role rather than the current stack's one anyway, it actually doesn't matter,
                # since the stack defining that iam_role won't actually be using that iam_role.
                self.logger.debug(
                    "Resolving iam_role requires the Stack connection manager. Temporarily setting "
                    "the iam_role to None until it can be fully resolved."
                )
                iam_role = None
                cache_connection_manager = False

            connection_manager = ConnectionManager(
                self.region,
                self.profile,
                self.external_name,
                iam_role,
                self.iam_role_session_duration,
            )
            if cache_connection_manager:
                self._connection_manager = connection_manager
            else:  # Return early without caching the connection manager.
                return connection_manager

        return self._connection_manager

    @property
    def template(self):
        """
        Returns the CloudFormation Template used to create the Stack.

        :returns: The Stack's template.
        :rtype: Template
        """
        if self._template is None:
            if self.template_path:
                handler_config = {"type": "file", "path": self.template_path}
            else:
                handler_config = self.template_handler_config

            self._template = Template(
                name=self.name,
                handler_config=handler_config,
                sceptre_user_data=self.sceptre_user_data,
                stack_group_config=self.stack_group_config,
                s3_details=self.s3_details,
                connection_manager=self.connection_manager,
            )
        return self._template
