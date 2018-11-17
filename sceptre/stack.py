# -*- coding: utf-8 -*-

"""
sceptre.stack

This module implements a Stack class, which stores a Stack's data.

"""

import logging

from sceptre.connection_manager import ConnectionManager
from sceptre.template import Template
from sceptre.helpers import get_external_stack_name
from sceptre.hooks import HookProperty
from sceptre.resolvers import ResolvableProperty


class Stack(object):
    """
    Stack stores information about a particular CloudFormation Stack.

    :param name: The name of the Stack.
    :type project: str

    :param project_code: A code which is prepended to the Stack names\
            of all Stacks built by Sceptre.
    :type project_code: str

    :param template_path: The relative path to the CloudFormation, Jinja2\
            or Python template to build the Stack from
    :type template_path: str

    :param region: The AWS region to build Stacks in.
    :type region: str

    :param parameters: The keys must match up with the name of the parameter.\
            The value must be of the type as defined in the template.
    :type parameters: str

    :param sceptre_user_data: Data passed into\
            `sceptre_handler(sceptre_user_data)` function in Python templates\
            or accessible under `sceptre_user_data` variable within Jinja2\
            templates.
    :type sceptre_user_data: dict

    :param hooks: A list of arbitrary shell or python commands or scripts to\
            run.
    :type hooks: sceptre.hooks.hook

    :param s3_details:
    :type s3_details: dict

    :param dependencies: The relative path to the Stack, including the file\
            extension of the Stack.
    :type dependencies: list

    :param role_arn: The ARN of a CloudFormation Service Role that is assumed\
            by CloudFormation to create, update or delete resources.
    :type role_arn: str

    :param protected: Stack protection against execution.
    :type protected: bool

    :param tags: CloudFormation Tags to be applied to the Stack.
    :type tags: dict

    :param external_name:
    :type external_name: str

    :param notifications: SNS topic ARNs to publish Stack related events to.\
            A maximum of 5 ARNs can be specified per Stack.
    :type notifications: list

    :param on_failure: This parameter describes the action taken by\
            CloudFormation when a Stack fails to create.
    :type on_failure: str

    :param profile: The name of the profile as defined in ~/.aws/config and\
            ~/.aws/credentials.
    :type profile: str

    :param stack_timeout: A timeout in minutes before considering the Stack\
            deployment as failed. After the specified timeout, the Stack will\
            be rolled back. Specifiyng zero, as well as ommiting the field,\
            will result in no timeout. Supports only positive integer value.
    :type stack_timeout: int
    """

    parameters = ResolvableProperty("parameters")
    sceptre_user_data = ResolvableProperty("sceptre_user_data")
    notifications = ResolvableProperty("notifications")
    hooks = HookProperty("hooks")

    def __init__(
        self, name, project_code, template_path, region, parameters=None,
        sceptre_user_data=None, hooks=None, s3_details=None,
        dependencies=None, role_arn=None, protected=False, tags=None,
        external_name=None, notifications=None, on_failure=None, profile=None,
        stack_timeout=0
    ):
        self.logger = logging.getLogger(__name__)

        self.name = name
        self.project_code = project_code
        self.region = region
        self.hooks = hooks

        self.external_name = external_name or \
            get_external_stack_name(self.project_code, self.name)

        self.template_path = template_path
        self.s3_details = s3_details
        self._template = None

        self.protected = protected
        self.role_arn = role_arn
        self.on_failure = on_failure
        self.dependencies = dependencies or []
        self.tags = tags or {}
        self.stack_timeout = stack_timeout
        self.profile = profile
        self.hooks = hooks or {}
        self.parameters = parameters or {}
        self.sceptre_user_data = sceptre_user_data or {}
        self.notifications = notifications or []

    def __repr__(self):
        return (
            "sceptre.stack.Stack("
            "name='{name}', project_code='{project_code}', "
            "template_path='{template_path}', region='{region}', "
            "profile='{profile}', parameters='{parameters}', "
            "sceptre_user_data='{sceptre_user_data}', "
            "hooks='{hooks}', s3_details='{s3_details}', "
            "dependencies='{dependencies}', role_arn='{role_arn}', "
            "protected='{protected}', tags='{tags}', "
            "external_name='{external_name}', "
            "notifications='{notifications}', on_failure='{on_failure}', "
            "stack_timeout='{stack_timeout}'"
            ")".format(
                name=self.name, project_code=self.project_code,
                template_path=self.template_path,
                region=self.region,
                profile=self.profile, parameters=self.parameters,
                sceptre_user_data=self.sceptre_user_data,
                hooks=self.hooks, s3_details=self.s3_details,
                dependencies=self.dependencies, role_arn=self.role_arn,
                protected=self.protected, tags=self.tags,
                external_name=self.external_name,
                notifications=self.notifications, on_failure=self.on_failure,
                stack_timeout=self.stack_timeout
            )
        )

    def __str__(self):
        return self.name

    @property
    def template(self):
        """
        Returns the CloudFormation Template used to create the Stack.

        :returns: The Stack's template.
        :rtype: str
        """
        self.connection_manager = ConnectionManager(
            self.region, self.profile, self.external_name
        )
        if self._template is None:
            self._template = Template(
                path=self.template_path,
                sceptre_user_data=self.sceptre_user_data,
                s3_details=self.s3_details,
                connection_manager=self.connection_manager
            )
        return self._template
