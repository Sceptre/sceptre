# -*- coding: utf-8 -*-

"""
sceptre.plan.actions

This module implements the StackActions class which provides the functionality
available to a Stack.
"""

import logging
import time

from os import path
from datetime import datetime, timedelta

import botocore
import json
from dateutil.tz import tzutc

from sceptre.connection_manager import ConnectionManager
from sceptre.hooks import add_stack_hooks
from sceptre.stack_status import StackStatus
from sceptre.stack_status import StackChangeSetStatus

from sceptre.exceptions import CannotUpdateFailedStackError
from sceptre.exceptions import UnknownStackStatusError
from sceptre.exceptions import UnknownStackChangeSetStatusError
from sceptre.exceptions import StackDoesNotExistError
from sceptre.exceptions import ProtectedStackError


class StackActions(object):
    """
    StackActions stores the operations a Stack can take, such as creating or
    deleting the Stack.

    :param stack: A Stack object
    :type stack: sceptre.stack.Stack
    """

    def __init__(self, stack):
        self.stack = stack
        self.name = self.stack.name
        self.logger = logging.getLogger(__name__)
        self.connection_manager = ConnectionManager(
            self.stack.region, self.stack.profile, self.stack.external_name
        )

    @add_stack_hooks
    def create(self):
        """
        Creates a Stack.

        :returns: The Stack's status.
        :rtype: sceptre.stack_status.StackStatus
        """
        self._protect_execution()
        self.logger.info("%s - Creating Stack", self.stack.name)
        create_stack_kwargs = {
            "StackName": self.stack.external_name,
            "Parameters": self._format_parameters(self.stack.parameters),
            "Capabilities": ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND'],
            "NotificationARNs": self.stack.notifications,
            "Tags": [
                {"Key": str(k), "Value": str(v)}
                for k, v in self.stack.tags.items()
            ]
        }

        if self.stack.on_failure:
            create_stack_kwargs.update({"OnFailure": self.stack.on_failure})
        create_stack_kwargs.update(
            self.stack.template.get_boto_call_parameter())
        create_stack_kwargs.update(self._get_role_arn())
        create_stack_kwargs.update(self._get_stack_timeout())

        try:
            response = self.connection_manager.call(
                service="cloudformation",
                command="create_stack",
                kwargs=create_stack_kwargs
            )

            self.logger.debug(
                "%s - Create stack response: %s", self.stack.name, response
            )

            status = self._wait_for_completion()
        except botocore.exceptions.ClientError as exp:
            if exp.response["Error"]["Code"] == "AlreadyExistsException":
                self.logger.info(
                    "%s - Stack already exists", self.stack.name
                )

                status = "COMPLETE"
            else:
                raise

        return status

    @add_stack_hooks
    def update(self):
        """
        Updates the Stack.

        :returns: The Stack's status.
        :rtype: sceptre.stack_status.StackStatus
        """
        self._protect_execution()
        self.logger.info("%s - Updating Stack", self.stack.name)
        update_stack_kwargs = {
            "StackName": self.stack.external_name,
            "Parameters": self._format_parameters(self.stack.parameters),
            "Capabilities": ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND'],
            "NotificationARNs": self.stack.notifications,
            "Tags": [
                {"Key": str(k), "Value": str(v)}
                for k, v in self.stack.tags.items()
            ]
        }
        update_stack_kwargs.update(
            self.stack.template.get_boto_call_parameter())
        update_stack_kwargs.update(self._get_role_arn())
        response = self.connection_manager.call(
            service="cloudformation",
            command="update_stack",
            kwargs=update_stack_kwargs
        )
        self.logger.debug(
            "%s - Update Stack response: %s", self.stack.name, response
        )

        status = self._wait_for_completion(self.stack.stack_timeout)
        # Cancel update after timeout
        if status == StackStatus.IN_PROGRESS:
            status = self.cancel_stack_update()

        return status

    def cancel_stack_update(self):
        """
        Cancels a Stack update.

        :returns: The cancelled Stack status.
        :rtype: sceptre.stack_status.StackStatus
        """
        self.logger.warning(
            "%s - Update Stack time exceeded the specified timeout",
            self.stack.name
        )
        response = self.connection_manager.call(
            service="cloudformation",
            command="cancel_update_stack",
            kwargs={"StackName": self.stack.external_name}
        )
        self.logger.debug(
            "%s - Cancel update Stack response: %s", self.stack.name, response
        )
        return self._wait_for_completion()

    def launch(self):
        """
        Launches the Stack.

        If the Stack status is create_failed or rollback_complete, the
        Stack is deleted. Launch then tries to create or update the Stack,
        depending if it already exists. If there are no updates to be
        performed, launch exits gracefully.

        :returns: The Stack's status.
        :rtype: sceptre.stack_status.StackStatus
        """
        self._protect_execution()
        self.logger.info("%s - Launching Stack", self.stack.name)
        try:
            existing_status = self._get_status()
        except StackDoesNotExistError:
            existing_status = "PENDING"

        self.logger.info(
            "%s - Stack is in the %s state", self.stack.name, existing_status
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
                        "%s - No updates to perform.", self.stack.name
                    )
                    status = StackStatus.COMPLETE
                else:
                    raise
        elif existing_status.endswith("IN_PROGRESS"):
            self.logger.info(
                "%s - Stack action is already in progress state and cannot "
                "be updated", self.stack.name
            )
            status = StackStatus.IN_PROGRESS
        elif existing_status.endswith("FAILED"):
            status = StackStatus.FAILED
            raise CannotUpdateFailedStackError(
                "'{0}' is in a the state '{1}' and cannot be updated".format(
                    self.stack.name, existing_status
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
        Deletes the Stack.

        :returns: The Stack's status.
        :rtype: sceptre.stack_status.StackStatus
        """
        self._protect_execution()

        self.logger.info("%s - Deleting stack", self.stack.name)
        try:
            status = self._get_status()
        except StackDoesNotExistError:
            self.logger.info("%s - Does not exist.", self.stack.name)
            status = StackStatus.COMPLETE
            return status

        delete_stack_kwargs = {"StackName": self.stack.external_name}
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
        self.logger.info("%s - delete %s", self.stack.name, status)
        return status

    def lock(self):
        """
        Locks the Stack by applying a deny-all updates Stack Policy.
        """
        policy_path = path.join(
            # need to get to the base install path. __file__ will take us into
            # sceptre/actions so need to walk up the path.
            path.abspath(path.join(__file__, "..", "..")),
            "stack_policies/lock.json"
        )
        self.set_policy(policy_path)
        self.logger.info("%s - Successfully locked Stack", self.stack.name)

    def unlock(self):
        """
        Unlocks the Stack by applying an allow-all updates Stack Policy.
        """
        policy_path = path.join(
            # need to get to the base install path. __file__ will take us into
            # sceptre/actions so need to walk up the path.
            path.abspath(path.join(__file__, "..", "..")),
            "stack_policies/unlock.json"
        )
        self.set_policy(policy_path)
        self.logger.info("%s - Successfully unlocked Stack", self.stack.name)

    def describe(self):
        """
        Returns the a description of the Stack.

        :returns: A Stack description.
        :rtype: dict
        """
        try:
            return self.connection_manager.call(
                service="cloudformation",
                command="describe_stacks",
                kwargs={"StackName": self.stack.external_name}
            )
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Message"].endswith("does not exist"):
                return
            raise

    def describe_events(self):
        """
        Returns the CloudFormation events for a Stack.

        :returns: CloudFormation events for a Stack.
        :rtype: dict
        """
        return self.connection_manager.call(
            service="cloudformation",
            command="describe_stack_events",
            kwargs={"StackName": self.stack.external_name}
        )

    def describe_resources(self):
        """
        Returns the logical and physical resource IDs of the Stack's resources.

        :returns: Information about the Stack's resources.
        :rtype: dict
        """
        self.logger.debug("%s - Describing stack resources", self.stack.name)
        try:
            response = self.connection_manager.call(
                service="cloudformation",
                command="describe_stack_resources",
                kwargs={"StackName": self.stack.external_name}
            )
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Message"].endswith("does not exist"):
                return {self.stack.name: []}
            raise

        self.logger.debug(
            "%s - Describe Stack resource response: %s",
            self.stack.name,
            response
        )

        desired_properties = ["LogicalResourceId", "PhysicalResourceId"]

        formatted_response = {self.stack.name: [
            {k: v for k, v in item.items() if k in desired_properties}
            for item in response["StackResources"]
        ]}
        return formatted_response

    def describe_outputs(self):
        """
        Returns the Stack's outputs.

        :returns: The Stack's outputs.
        :rtype: list
        """
        self.logger.debug("%s - Describing stack outputs", self.stack.name)

        try:
            response = self._describe()
        except botocore.exceptions.ClientError:
            return []

        return {self.stack.name: response["Stacks"][0].get("Outputs", [])}

    def continue_update_rollback(self):
        """
        Rolls back a Stack in the UPDATE_ROLLBACK_FAILED state to
        UPDATE_ROLLBACK_COMPLETE.
        """
        self.logger.debug("%s - Continuing update rollback", self.stack.name)
        continue_update_rollback_kwargs = {
            "StackName": self.stack.external_name
        }
        continue_update_rollback_kwargs.update(self._get_role_arn())
        self.connection_manager.call(
            service="cloudformation",
            command="continue_update_rollback",
            kwargs=continue_update_rollback_kwargs
        )
        self.logger.info(
            "%s - Successfully initiated continuation of update rollback",
            self.stack.name
        )

    def set_policy(self, policy_path):
        """
        Applies a Stack Policy.

        :param policy_path: The relative path of JSON file containing\
                the AWS Policy to apply.
        :type policy_path: str
        """
        with open(policy_path) as f:
            policy = f.read()

        self.logger.debug(
            "%s - Setting Stack policy: \n%s",
            self.stack.name,
            policy
        )

        self.connection_manager.call(
            service="cloudformation",
            command="set_stack_policy",
            kwargs={
                "StackName": self.stack.external_name,
                "StackPolicyBody": policy
            }
        )
        self.logger.info("%s - Successfully set Stack Policy", self.stack.name)

    def get_policy(self):
        """
        Returns a Stack's Policy.

        :returns: The Stack's Stack Policy.
        :rtype: str
        """
        self.logger.debug("%s - Getting Stack Policy", self.stack.name)
        response = self.connection_manager.call(
            service="cloudformation",
            command="get_stack_policy",
            kwargs={
                "StackName": self.stack.external_name
            }
        )
        json_formatting = json.loads(response.get(
            "StackPolicyBody", json.dumps("No Policy Information")))
        return {self.stack.name: json_formatting}

    def create_change_set(self, change_set_name):
        """
        Creates a Change Set with the name ``change_set_name``.

        :param change_set_name: The name of the Change Set.
        :type change_set_name: str
        """
        create_change_set_kwargs = {
            "StackName": self.stack.external_name,
            "Parameters": self._format_parameters(self.stack.parameters),
            "Capabilities": ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND'],
            "ChangeSetName": change_set_name,
            "NotificationARNs": self.stack.notifications,
            "Tags": [
                {"Key": str(k), "Value": str(v)}
                for k, v in self.stack.tags.items()
            ]
        }
        create_change_set_kwargs.update(
            self.stack.template.get_boto_call_parameter()
        )
        create_change_set_kwargs.update(self._get_role_arn())
        self.logger.debug(
            "%s - Creating Change Set '%s'", self.stack.name, change_set_name
        )
        self.connection_manager.call(
            service="cloudformation",
            command="create_change_set",
            kwargs=create_change_set_kwargs
        )
        # After the call successfully completes, AWS CloudFormation
        # starts creating the Change Set.
        self.logger.info(
            "%s - Successfully initiated creation of Change Set '%s'",
            self.stack.name, change_set_name
        )

    def delete_change_set(self, change_set_name):
        """
        Deletes the Change Set ``change_set_name``.

        :param change_set_name: The name of the Change Set.
        :type change_set_name: str
        """
        self.logger.debug(
            "%s - Deleting Change Set '%s'", self.stack.name, change_set_name
        )
        self.connection_manager.call(
            service="cloudformation",
            command="delete_change_set",
            kwargs={
                "ChangeSetName": change_set_name,
                "StackName": self.stack.external_name
            }
        )
        # If the call successfully completes, AWS CloudFormation
        # successfully deleted the Change Set.
        self.logger.info(
            "%s - Successfully deleted Change Set '%s'",
            self.stack.name, change_set_name
        )

    def describe_change_set(self, change_set_name):
        """
        Describes the Change Set ``change_set_name``.

        :param change_set_name: The name of the Change Set.
        :type change_set_name: str
        :returns: The description of the Change Set.
        :rtype: dict
        """
        self.logger.debug(
            "%s - Describing Change Set '%s'", self.stack.name, change_set_name
        )
        return self.connection_manager.call(
            service="cloudformation",
            command="describe_change_set",
            kwargs={
                "ChangeSetName": change_set_name,
                "StackName": self.stack.external_name
            }
        )

    def execute_change_set(self, change_set_name):
        """
        Executes the Change Set ``change_set_name``.

        :param change_set_name: The name of the Change Set.
        :type change_set_name: str
        :returns: The Stack status
        :rtype: str
        """
        self._protect_execution()
        self.logger.debug(
            "%s - Executing Change Set '%s'", self.stack.name, change_set_name
        )
        self.connection_manager.call(
            service="cloudformation",
            command="execute_change_set",
            kwargs={
                "ChangeSetName": change_set_name,
                "StackName": self.stack.external_name
            }
        )

        status = self._wait_for_completion()
        return status

    def list_change_sets(self):
        """
        Lists the Stack's Change Sets.

        :returns: The Stack's Change Sets.
        :rtype: dict or list
        """
        self.logger.debug("%s - Listing change sets", self.stack.name)
        try:
            response = self.connection_manager.call(
                service="cloudformation",
                command="list_change_sets",
                kwargs={
                    "StackName": self.stack.external_name
                }
            )
            return {self.stack.name: response.get("Summaries", [])}
        except botocore.exceptions.ClientError:
            return []

    def generate(self):
        """
        Returns the Template for the Stack
        """
        return self.stack.template.body

    def validate(self):
        """
        Validates the Stack's CloudFormation Template.

        Raises an error if the Template is invalid.

        :returns: Validation information about the Template.
        :rtype: dict
        :raises: botocore.exceptions.ClientError
        """
        self.logger.debug("%s - Validating Template", self.stack.name)
        response = self.connection_manager.call(
            service="cloudformation",
            command="validate_template",
            kwargs=self.stack.template.get_boto_call_parameter()
        )
        self.logger.debug(
            "%s - Validate Template response: %s", self.stack.name, response
        )
        return response

    def estimate_cost(self):
        """
        Estimates a Stack's cost.

        :returns: An estimate of the Stack's cost.
        :rtype: dict
        :raises: botocore.exceptions.ClientError
        """
        self.logger.debug("%s - Estimating template cost", self.stack.name)

        parameters = [
            {'ParameterKey': key, 'ParameterValue': value}
            for key, value in self.stack.parameters.items()
        ]

        kwargs = self.stack.template.get_boto_call_parameter()
        kwargs.update({'Parameters': parameters})

        response = self.connection_manager.call(
            service="cloudformation",
            command="estimate_template_cost",
            kwargs=kwargs
        )
        self.logger.debug(
            "%s - Estimate Stack cost response: %s", self.stack.name, response
        )
        return response

    def get_status(self):
        """
        Returns the Stack's status.

        :returns: The Stack's status.
        :rtype: sceptre.stack_status.StackStatus
        """
        try:
            return self._get_status()
        except StackDoesNotExistError:
            return "PENDING"

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

    def _get_role_arn(self):
        """
        Returns the Role ARN assumed by CloudFormation when building a Stack.

        Returns an empty dict if no Role is to be assumed.

        :returns: The a Role ARN
        :rtype: dict
        """
        if self.stack.role_arn:
            return {
                "RoleARN": self.stack.role_arn
            }
        else:
            return {}

    def _get_stack_timeout(self):
        """
        Return the timeout before considering the Stack to be failing.

        Returns an empty dict if no timeout is set.
        :returns: the creation/update timeout
        :rtype: dict
        """
        if self.stack.stack_timeout:
            return {
                "TimeoutInMinutes": self.stack.stack_timeout
            }
        else:
            return {}

    def _protect_execution(self):
        """
        Raises a ProtectedStackError if protect == True.

        :raises: sceptre.exceptions.ProtectedStackError
        """
        if self.stack.protected:
            raise ProtectedStackError(
                "Cannot perform action on '{0}': Stack protection is "
                "currently enabled".format(self.stack.name)
            )

    def _wait_for_completion(self, timeout=0):
        """
        Waits for a Stack operation to finish. Prints CloudFormation events
        while it waits.

        :param timeout: Timeout before returning, in minutes.

        :returns: The final Stack status.
        :rtype: sceptre.stack_status.StackStatus
        """
        timeout = 60 * timeout

        def timed_out(elapsed):
            return elapsed >= timeout if timeout else False

        status = StackStatus.IN_PROGRESS

        self.most_recent_event_datetime = (
            datetime.now(tzutc()) - timedelta(seconds=3)
        )
        elapsed = 0
        while status == StackStatus.IN_PROGRESS and not timed_out(elapsed):
            status = self._get_simplified_status(self._get_status())
            self._log_new_events()
            time.sleep(4)
            elapsed += 4

        return status

    def _describe(self):
        return self.connection_manager.call(
            service="cloudformation",
            command="describe_stacks",
            kwargs={"StackName": self.stack.external_name}
        )

    def _get_status(self):
        try:
            status = self._describe()["Stacks"][0]["StackStatus"]
        except botocore.exceptions.ClientError as exp:
            if exp.response["Error"]["Message"].endswith("does not exist"):
                raise StackDoesNotExistError(exp.response["Error"]["Message"])
            else:
                raise exp
        return status

    @staticmethod
    def _get_simplified_status(status):
        """
        Returns the simplified Stack Status.

        The simplified Stack status is represented by the struct
        ``sceptre.StackStatus()`` and can take one of the following options:

        * complete
        * in_progress
        * failed

        :param status: The CloudFormation Stack status to simplify.
        :type status: str
        :returns: The Stack's simplified status
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
        Log the latest Stack events while the Stack is being built.
        """
        events = self.describe_events()["StackEvents"]
        events.reverse()
        new_events = [
            event for event in events
            if event["Timestamp"] > self.most_recent_event_datetime
        ]
        for event in new_events:
            self.logger.info(" ".join([
                self.stack.name,
                event["LogicalResourceId"],
                event["ResourceType"],
                event["ResourceStatus"],
                event.get("ResourceStatusReason", "")
            ]))
            self.most_recent_event_datetime = event["Timestamp"]

    def wait_for_cs_completion(self, change_set_name):
        """
        Waits while the Stack Change Set status is "pending".

        :param change_set_name: The name of the Change Set.
        :type change_set_name: str
        :returns: The Change Set's status.
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
        Returns the status of a Change Set.

        :param change_set_name: The name of the Change Set.
        :type change_set_name: str
        :returns: The Change Set's status.
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
