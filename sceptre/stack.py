# -*- coding: utf-8 -*-

"""
sceptre.stack

This module implements a Stack class, which stores a Stack's data.

"""

import logging

from typing import List, Dict, Union, Any, Optional
from deprecation import deprecated

from sceptre import __version__
from sceptre.connection_manager import ConnectionManager
from sceptre.exceptions import InvalidConfigFileError
from sceptre.helpers import (
    get_external_stack_name,
    sceptreise_path,
    create_deprecated_alias_property,
)
from sceptre.hooks import Hook, HookProperty
from sceptre.resolvers import (
    ResolvableContainerProperty,
    ResolvableValueProperty,
    RecursiveResolve,
    PlaceholderType,
    Resolver,
)
from sceptre.template import Template


class Stack:
    """
    Stack stores information about a particular CloudFormation Stack.

    :param name: The name of the Stack.

    :param project_code: A code which is prepended to the Stack names\
            of all Stacks built by Sceptre.

    :param template_path: The relative path to the CloudFormation, Jinja2,
            or Python template to build the Stack from. If this is filled,
            `template_handler_config` should not be filled. This field has been deprecated since
            version 4.0.0 and will be removed eventually.

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

    :param s3_details: Details used for uploading templates to S3.

    :param dependencies: The relative path to the Stack, including the file\
            extension of the Stack.

    :param cloudformation_service_role: The ARN of a CloudFormation Service Role that is assumed\
            by CloudFormation to create, update or delete resources.

    :param protected: Stack protection against execution.

    :param tags: CloudFormation Tags to be applied to the Stack.

    :param external_name: The real stack name used for CloudFormation

    :param notifications: SNS topic ARNs to publish Stack related events to.\
            A maximum of 5 ARNs can be specified per Stack.

    :param on_failure: This parameter describes the action taken by\
            CloudFormation when a Stack fails to create.

    :param disable_rollback: If True, cloudformation will not rollback on deployment failures

    :param iam_role: The ARN of a role for Sceptre to assume before interacting
            with the environment. If not supplied, Sceptre uses the user's AWS CLI
            credentials. This field has been deprecated since version 4.0.0 and will be removed
            eventually.

    :param sceptre_role: The ARN of a role for Sceptre to assume before interacting\
            with the environment. If not supplied, Sceptre uses the user's AWS CLI\
            credentials.

    :param iam_role_session_duration: The duration in seconds of the assumed IAM role session.
            This field has been deprecated since version 4.0.0 and will be removed eventually.

    :param sceptre_role_session_duration: The duration in seconds of the assumed IAM role session.

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

    :param sceptre_role_session_duration: The session duration when Scetre assumes a role.\
           If not supplied, Sceptre uses default value (3600 seconds)

    :param stack_group_config: The StackGroup config for the Stack

    :param config: The complete config for the stack. Used by dump config.
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
    # Similarly, the placeholder_override=None for sceptre_role means that actions that would otherwise
    # use the sceptre_role will act as if there was no iam role when the sceptre_role stack has not been
    # deployed for commands that allow placeholders (like validate).
    sceptre_role = ResolvableValueProperty("sceptre_role", PlaceholderType.none)
    cloudformation_service_role = ResolvableValueProperty("cloudformation_service_role")

    hooks = HookProperty("hooks")

    iam_role = create_deprecated_alias_property(
        "iam_role",
        "sceptre_role",
        deprecated_in="4.0.0",
        removed_in=None,
    )
    role_arn = create_deprecated_alias_property(
        "role_arn",
        "cloudformation_service_role",
        deprecated_in="4.0.0",
        removed_in=None,
    )
    sceptre_role_session_duration = None
    iam_role_session_duration = create_deprecated_alias_property(
        "iam_role_session_duration",
        "sceptre_role_session_duration",
        deprecated_in="4.0.0",
        removed_in=None,
    )

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
        sceptre_role: str = None,
        iam_role: str = None,
        dependencies: List["Stack"] = None,
        cloudformation_service_role: str = None,
        role_arn: str = None,
        protected: bool = False,
        tags: dict = None,
        external_name: str = None,
        notifications: List[str] = None,
        on_failure: str = None,
        disable_rollback=False,
        profile: str = None,
        stack_timeout: int = 0,
        sceptre_role_session_duration: Optional[int] = None,
        iam_role_session_duration: Optional[int] = None,
        ignore=False,
        obsolete=False,
        stack_group_config: dict = None,
        config: dict = None,
    ):
        self.logger = logging.getLogger(__name__)

        self.name = sceptreise_path(name)
        self.project_code = project_code
        self.region = region
        self.required_version = required_version
        self.external_name = external_name or get_external_stack_name(
            self.project_code, self.name
        )
        self.dependencies = dependencies or []
        self.protected = protected
        self.on_failure = on_failure
        self.disable_rollback = self._ensure_boolean(
            "disable_rollback", disable_rollback
        )
        self.stack_group_config = stack_group_config or {}
        self.config = config or {}
        self.stack_timeout = stack_timeout
        self.profile = profile
        self.template_key_prefix = template_key_prefix
        self._set_field_with_deprecated_alias(
            "sceptre_role_session_duration",
            sceptre_role_session_duration,
            "iam_role_session_duration",
            iam_role_session_duration,
        )
        self.ignore = self._ensure_boolean("ignore", ignore)
        self.obsolete = self._ensure_boolean("obsolete", obsolete)

        self._template = None
        self._connection_manager = None

        # Resolvers and hooks need to be assigned last
        self.s3_details = s3_details
        self._set_field_with_deprecated_alias(
            "sceptre_role", sceptre_role, "iam_role", iam_role
        )
        self.tags = tags or {}
        self._set_field_with_deprecated_alias(
            "cloudformation_service_role",
            cloudformation_service_role,
            "role_arn",
            role_arn,
        )
        self.template_bucket_name = template_bucket_name
        self._set_field_with_deprecated_alias(
            "template_handler_config",
            template_handler_config,
            "template_path",
            template_path,
            required=True,
            preferred_config_name="template",
        )

        self.s3_details = s3_details
        self.parameters = self._cast_parameters(parameters or {})
        self.sceptre_user_data = sceptre_user_data or {}
        self.notifications = notifications or []

        self.hooks = hooks or {}

    def _ensure_boolean(self, config_name: str, value: Any) -> bool:
        if not isinstance(value, bool):
            raise InvalidConfigFileError(
                f"{self.name}: Value for {config_name} must be a boolean, not a {type(value).__name__}"
            )
        return value

    def _cast_parameters(
        self, parameters: Dict[str, Any]
    ) -> Dict[str, Union[str, List[Union[str, Resolver]], Resolver]]:
        """Cast CloudFormation parameters to valid types"""

        def cast_value(value: Any) -> Union[str, List[Union[str, Resolver]], Resolver]:
            if isinstance(value, bool):
                return "true" if value else "false"
            elif isinstance(value, (int, float)):
                return str(value)
            elif isinstance(value, list):
                return [cast_value(item) for item in value]
            elif isinstance(value, Resolver):
                return value
            return value

        def is_valid(value: Any) -> bool:
            return (
                isinstance(value, str)
                or (
                    isinstance(value, list)
                    and all(
                        isinstance(item, str) or isinstance(item, Resolver)
                        for item in value
                    )
                )
                or isinstance(value, Resolver)
            )

        if not isinstance(parameters, dict):
            raise InvalidConfigFileError(
                f"{self.name}: parameters must be a dictionary of key-value pairs, got {parameters}"
            )

        casted_parameters = {k: cast_value(v) for k, v in parameters.items()}

        if not all(is_valid(value) for value in casted_parameters.values()):
            raise InvalidConfigFileError(
                f"{self.name}: Values for parameters must be strings, lists or resolvers, got {casted_parameters}"
            )

        return casted_parameters

    def __repr__(self):
        return (
            "sceptre.stack.Stack("
            f"name='{self.name}', "
            f"project_code={self.project_code}, "
            f"template_handler_config={self.template_handler_config}, "
            f"region={self.region}, "
            f"template_bucket_name={self.template_bucket_name}, "
            f"template_key_prefix={self.template_key_prefix}, "
            f"required_version={self.required_version}, "
            f"sceptre_role={self.sceptre_role}, "
            f"sceptre_role_session_duration={self.sceptre_role_session_duration}, "
            f"profile={self.profile}, "
            f"sceptre_user_data={self.sceptre_user_data}, "
            f"parameters={self.parameters}, "
            f"hooks={self.hooks}, "
            f"s3_details={self.s3_details}, "
            f"dependencies={self.dependencies}, "
            f"cloudformation_service_role={self.cloudformation_service_role}, "
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
            and self.sceptre_role_session_duration
            == stack.sceptre_role_session_duration
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
                sceptre_role = self.sceptre_role
            except RecursiveResolve:
                # This would be the case when sceptre_role is set with a resolver (especially stack_output)
                # that uses the stack's connection manager. This creates a temporary condition where
                # you need the iam role to get the iam role. To get around this, it will temporarily
                # use None as the sceptre_role but will re-attempt to resolve the value in future accesses.
                # Since the Stack Output resolver (the most likely culprit) uses the target stack's
                # sceptre_role rather than the current stack's one anyway, it actually doesn't matter,
                # since the stack defining that sceptre_role won't actually be using that sceptre_role.
                self.logger.debug(
                    "Resolving sceptre_role requires the Stack connection manager. Temporarily setting "
                    "the sceptre_role to None until it can be fully resolved."
                )
                sceptre_role = None
                cache_connection_manager = False

            connection_manager = ConnectionManager(
                self.region,
                self.profile,
                self.external_name,
                sceptre_role,
                self.sceptre_role_session_duration,
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
            self._template = Template(
                name=self.name,
                handler_config=self.template_handler_config,
                sceptre_user_data=self.sceptre_user_data,
                stack_group_config=self.stack_group_config,
                s3_details=self.s3_details,
                connection_manager=self.connection_manager,
            )
        return self._template

    @property
    @deprecated(
        deprecated_in="4.0.0",
        removed_in=None,
        current_version=__version__,
        details="Use the template Stack Config key instead.",
    )
    def template_path(self) -> str:
        """The path argument from the template_handler config. This field is deprecated as of v4.0.0
        and will be removed in v5.0.0.
        """
        return self.template_handler_config["path"]

    @template_path.setter
    @deprecated(
        deprecated_in="4.0.0",
        removed_in=None,
        current_version=__version__,
        details="Use the template Stack Config key instead.",
    )
    def template_path(self, value: str):
        self.template_handler_config = {"type": "file", "path": value}

    def _set_field_with_deprecated_alias(
        self,
        preferred_attribute_name,
        preferred_value,
        deprecated_attribute_name,
        deprecated_value,
        *,
        required=False,
        preferred_config_name=None,
        deprecated_config_name=None,
    ):
        # This is a generic truthiness check. All current default values are falsy, so this should work.
        # If we ever use this function where the default value is NOT falsy, this will be a problem.
        preferred_config_name = preferred_config_name or preferred_attribute_name
        deprecated_config_name = deprecated_config_name or deprecated_attribute_name

        if preferred_value and deprecated_value:
            raise InvalidConfigFileError(
                f"Both '{preferred_config_name}' and '{deprecated_config_name}' are set. You should only set a "
                f"value for {preferred_config_name} because {deprecated_config_name} is deprecated."
            )
        elif preferred_value:
            setattr(self, preferred_attribute_name, preferred_value)
        elif deprecated_value:
            setattr(self, deprecated_attribute_name, deprecated_value)
        elif required:
            raise InvalidConfigFileError(
                f"{preferred_config_name} is a required Stack Config."
            )
        else:  # In case they're both falsy, we should just set the value using the preferred value.
            setattr(self, preferred_attribute_name, preferred_value)
