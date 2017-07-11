# -*- coding: utf-8 -*-

"""
sceptre.stack

This module implements a Stack class, which stores data and logic associated
with a particular stack.

"""

import datetime
import logging
import os
import time
import threading

from dateutil.tz import tzutc
import botocore

from .config import Config
from .resolvers import ResolvableProperty
from .stack_status import StackStatus
from .stack_status import StackChangeSetStatus
from .template import Template

from .hooks import add_stack_hooks
from .helpers import get_name_tuple
from .helpers import get_external_stack_name

from .exceptions import CannotUpdateFailedStackError
from .exceptions import UnknownStackStatusError
from .exceptions import UnknownStackChangeSetStatusError
from .exceptions import StackDoesNotExistError
from .exceptions import ProtectedStackError


class Stack(object):
    """
    Stack stores information about a particular CloudFormation stack.

    It implements methods for carrying out stack-level operations, such as
    creating or deleting the stack.

    :param name: The name of the stack.
    :type project: str
    :param environment_config: The stack's environment's config.
    :type environment_config: sceptre.config.Config
    :param connection_manager: A connection manager, used to make Boto3 calls.
    :type connection_manager: sceptre.connection_manager.ConnectionManager
    """
    _config_lock = threading.Lock()

    parameters = ResolvableProperty("parameters")
    sceptre_user_data = ResolvableProperty("sceptre_user_data")

    def __init__(self, name, environment_config, connection_manager):
        self.logger = logging.getLogger(__name__)

        self.name = name
        self.environment_config = environment_config

        self._environment_path = self.environment_config.environment_path
        self.project = self.environment_config["project_code"]
        self.region = self.environment_config["region"]

        self.connection_manager = connection_manager

        self._config = None
        self._template = None
        self._hooks = None
        self._dependencies = None
        self._external_name = None

    def __repr__(self):
        return (
            "sceptre.stack.Stack(stack_name='{0}', environment_config={1}, "
            "connection_manager={2})".format(
                self.name, self.environment_config, self.connection_manager
            )
        )

    @property
    def config(self):
        """
        Return's the stack's config.

        :returns: The stack's config.
        :rtype: sceptre.config.Config
        """
        if self._config is None:
            with self._config_lock:
                self._config = Config.with_yaml_constructors(
                    sceptre_dir=self.environment_config.sceptre_dir,
                    environment_path=self.environment_config.environment_path,
                    base_file_name=get_name_tuple(self.name)[-1],
                    environment_config=self.environment_config,
                    connection_manager=self.connection_manager
                )
                self._config.read(
                    self.environment_config.get("user_variables")
                )

        return self._config

    @property
    def dependencies(self):
        """
        Returns a list of stacks that this stack depends on.

        A list of stacks that need to exist in AWS to allow the creation of
        this stack.

        :returns: The dependent stacks.
        :rtype: list
        """
        if self._dependencies is None:
            self.logger.debug(
                "%s - Loading dependencies...", self.name
            )
            self._dependencies = set(
                self.config.get("dependencies", [])
            )
            self.logger.debug(
                "%s - Dependencies: %s", self.name, self._dependencies
            )
        return self._dependencies

    @property
    def hooks(self):
        """
        Returns the stack's hooks.

        Hooks are arbitraty pieces of code which are run before/after a stack
        create/update/delete.

        :returns: The stack's hooks.
        :rtype: dict
        """
        if self._hooks is None:
            self.logger.debug("%s - Loading hooks...", self._hooks)
            self._hooks = self.config.get("hooks", {})

        self.logger.debug("%s - Hooks: %s", self.name, self._hooks)
        return self._hooks

    @property
    def template(self):
        """
        Returns the CloudFormation template used to create the stack.

        :returns: The stack's template.
        :rtype: str
        """
        if self._template is None:
            abs_template_path = os.path.join(
                self.environment_config.sceptre_dir,
                self.config["template_path"],
            )

            self._template = Template(
                path=abs_template_path,
                sceptre_user_data=self.sceptre_user_data
            )
        return self._template

    @property
    def external_name(self):
        """
        Returns the stack_name specified in the stack config. If none is
        specified, it defaults to ``<project-code>-<stack-name>``.

        :returns: The stack's external name.
        :rtype: str
        """
        if self._external_name is None:
            self._external_name = self.config.get(
                "stack_name",
                get_external_stack_name(self.project, self.name)
            )
        return self._external_name

    @add_stack_hooks
    def create(self):
        """
        Creates the stack.

        :returns: The stack's status.
        :rtype: sceptre.stack_status.StackStatus
        """
        self._protect_execution()
        self.logger.info("%s - Creating stack", self.name)
        create_stack_kwargs = {
            "StackName": self.external_name,
            "Parameters": self._format_parameters(self.parameters),
            "Capabilities": ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
            "Tags": [
                {"Key": str(k), "Value": str(v)}
                for k, v in self.config.get("stack_tags", {}).items()
            ]
        }
        create_stack_kwargs.update(self._get_template_details())
        create_stack_kwargs.update(self._get_role_arn())
        response = self.connection_manager.call(
            service="cloudformation",
            command="create_stack",
            kwargs=create_stack_kwargs
        )
        self.logger.debug(
            "%s - Create stack response: %s", self.name, response
        )

        status = self._wait_for_completion()

        return status

    @add_stack_hooks
    def update(self):
        """
        Updates the stack.

        :returns: The stack's status.
        :rtype: sceptre.stack_status.StackStatus
        """
        self._protect_execution()
        self.logger.info("%s - Updating stack", self.name)
        update_stack_kwargs = {
            "StackName": self.external_name,
            "Parameters": self._format_parameters(self.parameters),
            "Capabilities": ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
            "Tags": [
                {"Key": str(k), "Value": str(v)}
                for k, v in self.config.get("stack_tags", {}).items()
            ]
        }
        update_stack_kwargs.update(self._get_template_details())
        update_stack_kwargs.update(self._get_role_arn())
        response = self.connection_manager.call(
            service="cloudformation",
            command="update_stack",
            kwargs=update_stack_kwargs
        )
        self.logger.debug(
            "%s - Update stack response: %s", self.name, response
        )

        status = self._wait_for_completion()

        return status

    def launch(self):
        """
        Launches the stack.

        If the stack status is create_complete or rollback_complete, the
        stack is deleted. Launch thena tries to create or update the stack,
        depending if it already exists. If there are no updates to be
        performed, launch exits gracefully.

        :returns: The stack's status.
        :rtype: sceptre.stack_status.StackStatus
        """
        self._protect_execution()
        self.logger.info("%s - Launching stack", self.name)
        try:
            existing_status = self.get_status()
        except StackDoesNotExistError:
            existing_status = "PENDING"

        self.logger.info(
            "%s - Stack is in the %s state", self.name, existing_status
        )

        if existing_status == "PENDING":
            status = self.create()
        elif existing_status in ["CREATE_FAILED", "ROLLBACK_COMPLETE"]:
            self.delete()
            status = self.create()
        elif existing_status.endswith("COMPLETE"):
            try:
                status = self.update()
            except botocore.exceptions.ClientError as exp:
                error_message = exp.response["Error"]["Message"]
                if error_message == "No updates are to be performed.":
                    self.logger.info(
                        "%s - No updates to perform.", self.name
                    )
                    status = StackStatus.COMPLETE
                else:
                    raise
            status = status
        elif existing_status.endswith("IN_PROGRESS"):
            self.logger.info(
                "%s - Stack action is already in progress state and cannot "
                "be updated", self.name
            )
            status = StackStatus.IN_PROGRESS
        elif existing_status.endswith("FAILED"):
            status = StackStatus.FAILED
            raise CannotUpdateFailedStackError(
                "'{0}' is in a the state '{1}' and cannot be updated".format(
                    self.name, existing_status
                )
            )
        else:
            raise UnknownStackStatusError(
                "{0} is unknown".format(existing_status)
            )
        return status

    @add_stack_hooks
    def delete(self):
        """
        Deletes the stack.

        :returns: The stack's status.
        :rtype: sceptre.stack_status.StackStatus
        """
        self._protect_execution()
        self.logger.info("%s - Deleting stack", self.name)
        try:
            status = self.get_status()
        except StackDoesNotExistError:
            self.logger.info("%s does not exist.", self.name)
            status = StackStatus.COMPLETE
            return status

        delete_stack_kwargs = {"StackName": self.external_name}
        delete_stack_kwargs.update(self._get_role_arn())
        self.connection_manager.call(
            service="cloudformation",
            command="delete_stack",
            kwargs=delete_stack_kwargs
        )

        try:
            status = self._wait_for_completion()
        except StackDoesNotExistError:
            status = StackStatus.COMPLETE
        except botocore.exceptions.ClientError as error:
            if error.response["Error"]["Message"].endswith("does not exist"):
                status = StackStatus.COMPLETE
            else:
                raise
        self.logger.info("%s - delete %s", self.name, status)
        return status

    def lock(self):
        """
        Locks the stack by applying a deny all updates stack policy.
        """
        policy_path = os.path.join(
            os.path.dirname(__file__),
            "stack_policies/lock.json"
        )
        self.set_policy(policy_path)
        self.logger.info("%s - Successfully locked stack", self.name)

    def unlock(self):
        """
        Unlocks the stack by applying an allow all updates stack policy.
        """
        policy_path = os.path.join(
            os.path.dirname(__file__),
            "stack_policies/unlock.json"
        )
        self.set_policy(policy_path)
        self.logger.info("%s - Successfully unlocked stack", self.name)

    def describe(self):
        """
        Returns the a description of the stack.

        :returns: A stack description.
        :rtype: dict
        """
        return self.connection_manager.call(
            service="cloudformation",
            command="describe_stacks",
            kwargs={"StackName": self.external_name}
        )

    def describe_events(self):
        """
        Returns a dictionary contianing the stack events.

        :returns: The CloudFormation events for a stack.
        :rtype: dict
        """
        return self.connection_manager.call(
            service="cloudformation",
            command="describe_stack_events",
            kwargs={"StackName": self.external_name}
        )

    def describe_resources(self):
        """
        Returns the logical and physical resource IDs of the stack's resources.

        :returns: Information about the stack's resources.
        :rtype: dict
        """
        self.logger.debug("%s - Describing stack resources", self.name)
        response = self.connection_manager.call(
            service="cloudformation",
            command="describe_stack_resources",
            kwargs={"StackName": self.external_name}
        )
        self.logger.debug(
            "%s - Describe stack resource response: %s", self.name, response
        )

        desired_properties = ["LogicalResourceId", "PhysicalResourceId"]

        formatted_response = [
            {k: v for k, v in item.items() if k in desired_properties}
            for item in response["StackResources"]
        ]
        return formatted_response

    def describe_outputs(self):
        """
        Returns a list of stack outputs.

        :returns: The stack's outputs.
        :rtype: list
        """
        self.logger.debug("%s - Describing stack outputs", self.name)
        response = self.describe()

        return response["Stacks"][0].get("Outputs", [])

    def continue_update_rollback(self):
        """
        Rolls back a stack in the UPDATE_ROLLBACK_FAILED state to
        UPDATE_ROLLBACK_COMPLETE.
        """
        self.logger.debug("%s - Continuing update rollback", self.name)
        continue_update_rollback_kwargs = {"StackName": self.external_name}
        continue_update_rollback_kwargs.update(self._get_role_arn())
        self.connection_manager.call(
            service="cloudformation",
            command="continue_update_rollback",
            kwargs=continue_update_rollback_kwargs
        )
        self.logger.info(
            "%s - Successfully initiated continuation of update rollback",
            self.name
        )

    def set_policy(self, policy_path):
        """
        Applies a stack policy.

        :param policy_path: the path of json file containing a aws policy
        :type policy_path: str
        """
        with open(policy_path) as f:
            policy = f.read()

        self.logger.debug("%s - Setting stack policy: \n%s", self.name, policy)
        self.connection_manager.call(
            service="cloudformation",
            command="set_stack_policy",
            kwargs={
                "StackName": self.external_name,
                "StackPolicyBody": policy
            }
        )
        self.logger.info("%s - Successfully set stack policy", self.name)

    def get_policy(self):
        """
        Returns a stack's policy.

        :returns: The stack's stack policy.
        :rtype: str
        """
        self.logger.debug("%s - Getting stack policy", self.name)
        response = self.connection_manager.call(
            service="cloudformation",
            command="get_stack_policy",
            kwargs={
                "StackName": self.external_name
            }
        )

        return response

    def validate_template(self):
        """
        Validates the stack's CloudFormation template.

        Raises an error if the template is invalid.

        :returns: Information about the template.
        :rtype: dict
        :raises: botocore.exceptions.ClientError
        """
        self.logger.debug("%s - Validating template", self.name)
        response = self.connection_manager.call(
            service="cloudformation",
            command="validate_template",
            kwargs=self._get_template_details()
        )
        self.logger.debug(
            "%s - Validate template response: %s", self.name, response
        )
        return response

    def create_change_set(self, change_set_name):
        """
        Creates a change set with the name ``change_set_name``.

        :param change_set_name: The name of the change set.
        :type change_set_name: str
        """
        create_change_set_kwargs = {
            "StackName": self.external_name,
            "Parameters": self._format_parameters(self.parameters),
            "Capabilities": ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
            "ChangeSetName": change_set_name,
            "Tags": [
                {"Key": str(k), "Value": str(v)}
                for k, v in self.config.get("stack_tags", {}).items()
            ]
        }
        create_change_set_kwargs.update(self._get_template_details())
        create_change_set_kwargs.update(self._get_role_arn())
        self.logger.debug(
            "%s - Creating change set '%s'", self.name, change_set_name
        )
        self.connection_manager.call(
            service="cloudformation",
            command="create_change_set",
            kwargs=create_change_set_kwargs
        )
        # After the call successfully completes, AWS CloudFormation
        # starts creating the change set.
        self.logger.info(
            "%s - Successfully initiated creation of change set '%s'",
            self.name, change_set_name
        )

    def delete_change_set(self, change_set_name):
        """
        Deletes the change set ``change_set_name``.

        :param change_set_name: The name of the change set.
        :type change_set_name: str
        """
        self.logger.debug(
            "%s - Deleting change set '%s'", self.name, change_set_name
        )
        self.connection_manager.call(
            service="cloudformation",
            command="delete_change_set",
            kwargs={
                "ChangeSetName": change_set_name,
                "StackName": self.external_name
            }
        )
        # If the call successfully completes, AWS CloudFormation
        # successfully deleted the change set.
        self.logger.info(
            "%s - Successfully deleted change set '%s'",
            self.name, change_set_name
        )

    def describe_change_set(self, change_set_name):
        """
        Describes the change set ``change_set_name``.

        :param change_set_name: The name of the change set.
        :type change_set_name: str
        :returns: The description of the change set.
        :rtype: dict
        """
        self.logger.debug(
            "%s - Describing change set '%s'", self.name, change_set_name
        )
        return self.connection_manager.call(
            service="cloudformation",
            command="describe_change_set",
            kwargs={
                "ChangeSetName": change_set_name,
                "StackName": self.external_name
            }
        )

    def execute_change_set(self, change_set_name):
        """
        Executes the change set ``change_set_name``.

        :param change_set_name: The name of the change set.
        :type change_set_name: str
        """
        self._protect_execution()
        self.logger.debug(
            "%s - Executing change set '%s'", self.name, change_set_name
        )
        self.connection_manager.call(
            service="cloudformation",
            command="execute_change_set",
            kwargs={
                "ChangeSetName": change_set_name,
                "StackName": self.external_name
            }
        )

        status = self._wait_for_completion()
        return status

    def list_change_sets(self):
        """
        Lists the stack's change sets.

        :returns: The stack's change sets.
        :rtype: dict
        """
        self.logger.debug("%s - Listing change sets", self.name)
        return self.connection_manager.call(
            service="cloudformation",
            command="list_change_sets",
            kwargs={
                "StackName": self.external_name
            }
        )

    def get_status(self):
        """
        Returns the stack's status.

        :returns: The stack's status.
        :rtype: sceptre.stack_status.StackStatus
        :raises: sceptre.exceptions.StackDoesNotExistError
        """
        try:
            status = self.describe()["Stacks"][0]["StackStatus"]
        except botocore.exceptions.ClientError as exp:
            if exp.response["Error"]["Message"].endswith("does not exist"):
                raise StackDoesNotExistError(exp.response["Error"]["Message"])
            else:
                raise exp
        return status

    def _format_parameters(self, parameters):
        """
        Converts CloudFormation parameters to the format used by Boto3.

        :param parameters: A dictionary of parameters.
        :type parameters: dict
        :returns: A list of the formatted parameters.
        :rtype: list
        """
        formatted_parameters = []
        for name, value in parameters.items():
            if value is None:
                continue
            if isinstance(value, list):
                value = ",".join(value)
            formatted_parameters.append({
                "ParameterKey": name,
                "ParameterValue": value
            })

        return formatted_parameters

    def _get_template_details(self):
        """
        Returns the CloudFormation template location.

        Uploads the template to S3 and returns the object's URL, or returns
        the template itself.

        :returns: The location of the template.
        :rtype: dict
        """
        if "template_bucket_name" in self.environment_config:
            template_url = self.template.upload_to_s3(
                self.region,
                self.environment_config["template_bucket_name"],
                self.environment_config.get("template_key_prefix", ""),
                self._environment_path,
                self.external_name,
                self.connection_manager
            )
            return {"TemplateURL": template_url}
        else:
            return {"TemplateBody": self.template.body}

    def _get_role_arn(self):
        """
        Returns the role arn assumed by CloudFormation when building a stack.

        Returns an empty dict if no role is to be assumed.

        :returns: the a role arn
        :rtype: dict
        """
        if "role_arn" in self.config:
            return {
                "RoleARN": self.config["role_arn"]
            }
        else:
            return {}

    def _protect_execution(self):
        """
        Raises a ProtectedStackError if protect == True.
        This error is meant to stop the

        :raises: sceptre.exceptions.ProtectedStackError
        """
        if self.config.get("protect", False):
            raise ProtectedStackError(
                "Cannot perform action on '{0}': stack protection is "
                "currently enabled".format(self.name)
            )

    def _wait_for_completion(self):
        """
        Waits for a stack operation to finish. Prints CloudFormation events
        while it waits.

        :returns: The final stack status.
        :rtype: sceptre.stack_status.StackStatus
        """
        status = StackStatus.IN_PROGRESS

        self.most_recent_event_datetime = (
            datetime.datetime.now(tzutc()) - datetime.timedelta(seconds=3)
        )
        while status == StackStatus.IN_PROGRESS:
            status = self._get_simplified_status(self.get_status())
            self._log_new_events()
            time.sleep(4)
        return status

    @staticmethod
    def _get_simplified_status(status):
        """
        Returns the simplified Stack Status.

        The simplified stack status is represented by the struct
        ``sceptre.StackStatus()`` and can take one of the following options:

        * complete
        * in_progress
        * failed

        :param status: The CloudFormation stack status to simplify.
        :type status: str
        :returns: The stack's simplified status
        :rtype: sceptre.stack_status.StackStatus
        """
        if status.endswith("ROLLBACK_COMPLETE"):
            return StackStatus.FAILED
        elif status.endswith("_COMPLETE"):
            return StackStatus.COMPLETE
        elif status.endswith("_IN_PROGRESS"):
            return StackStatus.IN_PROGRESS
        elif status.endswith("_FAILED"):
            return StackStatus.FAILED
        else:
            raise UnknownStackStatusError(
                "{0} is unknown".format(status)
            )

    def _log_new_events(self):
        """
        Log the latest stack events while the stack is being built.
        """
        events = self.describe_events()["StackEvents"]
        events.reverse()
        new_events = [
            event for event in events
            if event["Timestamp"] > self.most_recent_event_datetime
        ]
        for event in new_events:
            self.logger.info(" ".join([
                event["Timestamp"].replace(microsecond=0).isoformat(),
                self.name,
                event["LogicalResourceId"],
                event["ResourceType"],
                event["ResourceStatus"],
                event.get("ResourceStatusReason", "")
            ]))
            self.most_recent_event_datetime = event["Timestamp"]

    def wait_for_cs_completion(self, change_set_name):
        """
        Waits while the stack change set status is "pending".

        :param change_set_name: The name of the change set.
        :type change_set_name: str
        :returns: The change set's status.
        :rtype: sceptre.stack_status.StackChangeSetStatus
        """
        while True:
            status = self._get_cs_status(change_set_name)
            if status != StackChangeSetStatus.PENDING:
                break
            time.sleep(2)

        return status

    def _get_cs_status(self, change_set_name):
        """
        Returns the status of a change set.

        :param change_set_name: The name of the change set.
        :type change_set_name: str
        :returns: The change set's status.
        :rtype: sceptre.stack_status.StackChangeSetStatus
        """
        cs_description = self.describe_change_set(change_set_name)

        cs_status = cs_description["Status"]
        cs_exec_status = cs_description["ExecutionStatus"]
        possible_statuses = [
            "CREATE_PENDING", "CREATE_IN_PROGRESS",
            "CREATE_COMPLETE", "DELETE_COMPLETE", "FAILED"
        ]
        possible_execution_statuses = [
            "UNAVAILABLE", "AVAILABLE", "EXECUTE_IN_PROGRESS",
            "EXECUTE_COMPLETE", "EXECUTE_FAILED", "OBSOLETE"
        ]

        if cs_status not in possible_statuses:
            raise UnknownStackChangeSetStatusError(
                "Status {0} is unknown".format(cs_status)
            )
        if cs_exec_status not in possible_execution_statuses:
            raise UnknownStackChangeSetStatusError(
                "ExecutionStatus {0} is unknown".format(cs_status)
            )

        if (
                cs_status == "CREATE_COMPLETE" and
                cs_exec_status == "AVAILABLE"
        ):
            return StackChangeSetStatus.READY
        elif (
                cs_status in [
                    "CREATE_PENDING", "CREATE_IN_PROGRESS", "CREATE_COMPLETE"
                ] and
                cs_exec_status in ["UNAVAILABLE", "AVAILABLE"]
        ):
            return StackChangeSetStatus.PENDING
        elif (
                cs_status in ["DELETE_COMPLETE", "FAILED"] or
                cs_exec_status in [
                    "EXECUTE_IN_PROGRESS", "EXECUTE_COMPLETE",
                    "EXECUTE_FAILED", "OBSOLETE"
                ]
        ):
            return StackChangeSetStatus.DEFUNCT
        else:  # pragma: no cover
            raise Exception("This else should not be reachable.")
