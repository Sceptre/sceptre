# -*- coding: utf-8 -*-

"""
sceptre.stack

This module implements a Stack class, which stores data and logic associated
with a particular stack.

"""

import logging

from sceptre.connection_manager import ConnectionManager
from sceptre.template import Template
from sceptre.helpers import get_external_stack_name
from sceptre.hooks import HookProperty
from sceptre.resolvers import ResolvableProperty


class Stack(object):
    """
    Stack stores information about a particular CloudFormation stack.

    It implements methods for carrying out stack-level operations, such as
    creating or deleting the stack.

    :param name: The name of the stack.
    :type project: str
    :param connection_manager: A connection manager, used to make Boto3 calls.
    :type connection_manager: sceptre.connection_manager.ConnectionManager
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
        Returns the CloudFormation template used to create the stack.

        :returns: The stack's template.
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
