# -*- coding: utf-8 -*-

"""
sceptre.plan.actions

This module implements the StackActions class which provides the functionality
available to a Stack.
"""

import json
import logging
import time
import typing
import urllib
import botocore

from datetime import datetime, timedelta
from dateutil.tz import tzutc
from os import path

from sceptre.connection_manager import ConnectionManager

from sceptre.exceptions import (
    CannotUpdateFailedStackError,
    ProtectedStackError,
    StackDoesNotExistError,
    UnknownStackChangeSetStatusError,
    UnknownStackStatusError,
)
from sceptre.helpers import extract_datetime_from_aws_response_headers
from sceptre.hooks import add_stack_hooks, add_stack_hooks_with_aliases
from sceptre.stack import Stack
from sceptre.stack_status import StackChangeSetStatus, StackStatus

from typing import Dict, Optional, Tuple, Union

if typing.TYPE_CHECKING:
    from sceptre.diffing.stack_differ import StackDiff, StackDiffer


class StackActions:
    """
    StackActions stores the operations a Stack can take, such as creating or
    deleting the Stack.

    :param stack: A Stack object
    :type stack: sceptre.stack.Stack
    """

    def __init__(self, stack: Stack):
        self.stack = stack
        self.name = self.stack.name
        self.logger = logging.getLogger(__name__)
        self.connection_manager = ConnectionManager(
            self.stack.region,
            self.stack.profile,
            self.stack.external_name,
            self.stack.sceptre_role,
            self.stack.sceptre_role_session_duration,
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
            "Capabilities": [
                "CAPABILITY_IAM",
                "CAPABILITY_NAMED_IAM",
                "CAPABILITY_AUTO_EXPAND",
            ],
            "NotificationARNs": self.stack.notifications,
            "Tags": [
                {"Key": str(k), "Value": str(v)} for k, v in self.stack.tags.items()
            ],
        }

        # can specify either DisableRollback or OnFailure , but not both
        if self.stack.disable_rollback:
            create_stack_kwargs.update({"DisableRollback": self.stack.disable_rollback})
        elif self.stack.on_failure:
            create_stack_kwargs.update({"OnFailure": self.stack.on_failure})

        create_stack_kwargs.update(self.stack.template.get_boto_call_parameter())
        create_stack_kwargs.update(self._get_role_arn())
        create_stack_kwargs.update(self._get_stack_timeout())

        try:
            response = self.connection_manager.call(
                service="cloudformation",
                command="create_stack",
                kwargs=create_stack_kwargs,
            )

            self.logger.debug(
                "%s - Create stack response: %s", self.stack.name, response
            )

            status = self._wait_for_completion(boto_response=response)
        except botocore.exceptions.ClientError as exp:
            if exp.response["Error"]["Code"] == "AlreadyExistsException":
                self.logger.info("%s - Stack already exists", self.stack.name)

                status = StackStatus.COMPLETE
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
        try:
            update_stack_kwargs = {
                "StackName": self.stack.external_name,
                "Parameters": self._format_parameters(self.stack.parameters),
                "Capabilities": [
                    "CAPABILITY_IAM",
                    "CAPABILITY_NAMED_IAM",
                    "CAPABILITY_AUTO_EXPAND",
                ],
                "NotificationARNs": self.stack.notifications,
                "Tags": [
                    {"Key": str(k), "Value": str(v)} for k, v in self.stack.tags.items()
                ],
            }

            if self.stack.disable_rollback:
                update_stack_kwargs.update(
                    {"DisableRollback": self.stack.disable_rollback}
                )

            update_stack_kwargs.update(self.stack.template.get_boto_call_parameter())
            update_stack_kwargs.update(self._get_role_arn())
            response = self.connection_manager.call(
                service="cloudformation",
                command="update_stack",
                kwargs=update_stack_kwargs,
            )
            status = self._wait_for_completion(
                self.stack.stack_timeout, boto_response=response
            )
            self.logger.debug(
                "%s - Update Stack response: %s", self.stack.name, response
            )

            # Cancel update after timeout
            if status == StackStatus.IN_PROGRESS:
                status = self.cancel_stack_update()

            return status
        except botocore.exceptions.ClientError as exp:
            error_message = exp.response["Error"]["Message"]
            if error_message == "No updates are to be performed.":
                self.logger.info("%s - No updates to perform.", self.stack.name)
                return StackStatus.COMPLETE
            else:
                raise

    def cancel_stack_update(self):
        """
        Cancels a Stack update.

        :returns: The cancelled Stack status.
        :rtype: sceptre.stack_status.StackStatus
        """
        self.logger.warning(
            "%s - Update Stack time exceeded the specified timeout", self.stack.name
        )
        response = self.connection_manager.call(
            service="cloudformation",
            command="cancel_update_stack",
            kwargs={"StackName": self.stack.external_name},
        )
        self.logger.debug(
            "%s - Cancel update Stack response: %s", self.stack.name, response
        )
        return self._wait_for_completion(boto_response=response)

    @add_stack_hooks
    def launch(self) -> StackStatus:
        """
        Launches the Stack.

        If the Stack status is create_failed or rollback_complete, the
        Stack is deleted. Launch then tries to create or update the Stack,
        depending if it already exists. If there are no updates to be
        performed, launch exits gracefully.

        :returns: The Stack's status.
        """
        self._protect_execution()
        self.logger.info(f"{self.stack.name} - Launching Stack")

        try:
            existing_status = self._get_status()
        except StackDoesNotExistError:
            existing_status = "PENDING"

        self.logger.info(
            "%s - Stack is in the %s state", self.stack.name, existing_status
        )

        if existing_status == "PENDING":
            status = self.create()
        elif existing_status in [
            "CREATE_FAILED",
            "ROLLBACK_COMPLETE",
            "REVIEW_IN_PROGRESS",
        ]:
            self.delete()
            status = self.create()
        elif existing_status.endswith("COMPLETE"):
            status = self.update()
        elif existing_status.endswith("IN_PROGRESS"):
            self.logger.info(
                "%s - Stack action is already in progress state and cannot "
                "be updated",
                self.stack.name,
            )
            status = StackStatus.IN_PROGRESS
        elif existing_status.endswith("FAILED"):
            raise CannotUpdateFailedStackError(
                "'{0}' is in a the state '{1}' and cannot be updated".format(
                    self.stack.name, existing_status
                )
            )
        else:
            raise UnknownStackStatusError("{0} is unknown".format(existing_status))
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
        response = self.connection_manager.call(
            service="cloudformation", command="delete_stack", kwargs=delete_stack_kwargs
        )

        try:
            status = self._wait_for_completion(boto_response=response)
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
            "stack_policies/lock.json",
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
            "stack_policies/unlock.json",
        )
        self.set_policy(policy_path)
        self.logger.info("%s - Successfully unlocked Stack", self.stack.name)

    def describe(self):
        """
        Returns the a description of the Stack.

        :returns: A Stack description.
        :rtype: dict
        """
        return self.connection_manager.call(
            service="cloudformation",
            command="describe_stacks",
            kwargs={"StackName": self.stack.external_name},
        )

    def describe_events(self):
        """
        Returns the CloudFormation events for a Stack.

        :returns: CloudFormation events for a Stack.
        :rtype: dict
        """
        return self.connection_manager.call(
            service="cloudformation",
            command="describe_stack_events",
            kwargs={"StackName": self.stack.external_name},
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
                kwargs={"StackName": self.stack.external_name},
            )
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Message"].endswith("does not exist"):
                return {self.stack.name: []}
            raise

        self.logger.debug(
            "%s - Describe Stack resource response: %s", self.stack.name, response
        )

        desired_properties = ["LogicalResourceId", "PhysicalResourceId"]

        formatted_response = {
            self.stack.name: [
                {k: v for k, v in item.items() if k in desired_properties}
                for item in response["StackResources"]
            ]
        }
        return formatted_response

    def describe_outputs(self):
        """
        Returns the Stack's outputs.

        :returns: The stack's outputs.
        :rtype: list
        """
        self.logger.debug("%s - Describing stack outputs", self.stack.name)
        response = self.describe()

        return {self.stack.name: response["Stacks"][0].get("Outputs", [])}

    def continue_update_rollback(self):
        """
        Rolls back a Stack in the UPDATE_ROLLBACK_FAILED state to
        UPDATE_ROLLBACK_COMPLETE.
        """
        self.logger.debug("%s - Continuing update rollback", self.stack.name)
        continue_update_rollback_kwargs = {"StackName": self.stack.external_name}
        continue_update_rollback_kwargs.update(self._get_role_arn())
        self.connection_manager.call(
            service="cloudformation",
            command="continue_update_rollback",
            kwargs=continue_update_rollback_kwargs,
        )
        self.logger.info(
            "%s - Successfully initiated continuation of update rollback",
            self.stack.name,
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

        self.logger.debug("%s - Setting Stack policy: \n%s", self.stack.name, policy)

        self.connection_manager.call(
            service="cloudformation",
            command="set_stack_policy",
            kwargs={"StackName": self.stack.external_name, "StackPolicyBody": policy},
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
            kwargs={"StackName": self.stack.external_name},
        )
        json_formatting = json.loads(
            response.get("StackPolicyBody", json.dumps("No Policy Information"))
        )
        return {self.stack.name: json_formatting}

    @add_stack_hooks
    def create_change_set(self, change_set_name):
        """
        Creates a Change Set with the name ``change_set_name``.

        :param change_set_name: The name of the Change Set.
        :type change_set_name: str
        """
        try:
            existing_status = self._get_status()
        except StackDoesNotExistError:
            existing_status = "PENDING"

        self.logger.info(
            "%s - Stack is in the %s state", self.stack.name, existing_status
        )

        change_set_type = (
            "CREATE"
            if existing_status in ["PENDING", "REVIEW_IN_PROGRESS"]
            else "UPDATE"
        )

        create_change_set_kwargs = {
            "StackName": self.stack.external_name,
            "Parameters": self._format_parameters(self.stack.parameters),
            "Capabilities": [
                "CAPABILITY_IAM",
                "CAPABILITY_NAMED_IAM",
                "CAPABILITY_AUTO_EXPAND",
            ],
            "ChangeSetName": change_set_name,
            "ChangeSetType": change_set_type,
            "NotificationARNs": self.stack.notifications,
            "Tags": [
                {"Key": str(k), "Value": str(v)} for k, v in self.stack.tags.items()
            ],
        }

        create_change_set_kwargs.update(self.stack.template.get_boto_call_parameter())
        create_change_set_kwargs.update(self._get_role_arn())

        try:
            self._create_change_set(change_set_name, create_change_set_kwargs)
        except Exception as err:
            self.logger.info(
                "%s - Failed creating Change Set '%s'\n%s",
                self.stack.name,
                change_set_name,
                err,
            )

    def _create_change_set(self, change_set_name, create_change_set_kwargs):
        self.logger.debug(
            "%s - Creating Change Set '%s'", self.stack.name, change_set_name
        )
        self.connection_manager.call(
            service="cloudformation",
            command="create_change_set",
            kwargs=create_change_set_kwargs,
        )
        # After the call successfully completes, AWS CloudFormation
        # starts creating the Change Set.
        self.logger.info(
            "%s - Successfully initiated creation of Change Set '%s'",
            self.stack.name,
            change_set_name,
        )

    def delete_change_set(self, change_set_name):
        """
        Deletes the Change Set ``change_set_name``.

        :param change_set_name: The name of the Change Set.
        :type change_set_name: str
        """
        # If the call successfully completes, AWS CloudFormation
        # successfully deleted the Change Set.
        try:
            self._delete_change_set(change_set_name)
            self.logger.info(
                "%s - Successfully deleted Change Set '%s'",
                self.stack.name,
                change_set_name,
            )
        except Exception as err:
            self.logger.info(
                "%s - Failed deleting Change Set '%s'\n%s",
                self.stack.name,
                change_set_name,
                err,
            )

    def _delete_change_set(self, change_set_name):
        self.logger.debug(
            "%s - Deleting Change Set '%s'", self.stack.name, change_set_name
        )
        self.connection_manager.call(
            service="cloudformation",
            command="delete_change_set",
            kwargs={
                "ChangeSetName": change_set_name,
                "StackName": self.stack.external_name,
            },
        )

    def describe_change_set(self, change_set_name):
        """
        Describes the Change Set ``change_set_name``.

        :param change_set_name: The name of the Change Set.
        :type change_set_name: str
        :returns: The description of the Change Set.
        :rtype: dict
        """
        return_val = {}

        try:
            return_val = self._describe_change_set(change_set_name)
        except Exception as err:
            self.logger.info(
                "%s - Failed describing Change Set '%s'\n%s",
                self.stack.name,
                change_set_name,
                err,
            )

        return return_val

    def _describe_change_set(self, change_set_name):
        self.logger.debug(
            "%s - Describing Change Set '%s'", self.stack.name, change_set_name
        )
        return self.connection_manager.call(
            service="cloudformation",
            command="describe_change_set",
            kwargs={
                "ChangeSetName": change_set_name,
                "StackName": self.stack.external_name,
            },
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
        change_set = self.describe_change_set(change_set_name)
        status = change_set.get("Status")
        reason = change_set.get("StatusReason")

        return_val = 0

        if status == "FAILED" and self._change_set_creation_failed_due_to_no_changes(
            reason
        ):
            self.logger.info(
                "Skipping ChangeSet on Stack: {} - there are no changes".format(
                    change_set.get("StackName")
                )
            )
            return return_val

        try:
            return_val = self._execute_change_set(change_set_name)
        except Exception as err:
            self.logger.info(
                "%s - Failed describing Change Set '%s'\n%s",
                self.stack.name,
                change_set_name,
                err,
            )

        return return_val

    def _execute_change_set(self, change_set_name):
        self.logger.debug(
            "%s - Executing Change Set '%s'", self.stack.name, change_set_name
        )
        response = self.connection_manager.call(
            service="cloudformation",
            command="execute_change_set",
            kwargs={
                "ChangeSetName": change_set_name,
                "StackName": self.stack.external_name,
            },
        )
        status = self._wait_for_completion(boto_response=response)
        return status

    def _change_set_creation_failed_due_to_no_changes(self, reason: str) -> bool:
        """
        Indicates the change set failed when it was created because there were actually
        no changes introduced from the change set.

        :param reason: The reason reported by CloudFormation for the Change Set failure
        """
        reason = reason.lower()
        no_change_substrings = (
            "submitted information didn't contain changes",
            "no updates are to be performed",  # The reason returned for SAM templates
        )

        for substring in no_change_substrings:
            if substring in reason:
                return True
        return False

    def list_change_sets(self, url=False):
        """
        Lists the Stack's Change Sets.

        :param url: Write out a console URL instead.
        :type url: bool

        :returns: The Stack's Change Sets.
        :rtype: dict or list
        """
        response = self._list_change_sets()
        summaries = response.get("Summaries", [])

        if url:
            summaries = self._convert_to_url(summaries)

        return {self.stack.name: summaries}

    def _list_change_sets(self):
        self.logger.debug("%s - Listing change sets", self.stack.name)
        try:
            return self.connection_manager.call(
                service="cloudformation",
                command="list_change_sets",
                kwargs={"StackName": self.stack.external_name},
            )
        except botocore.exceptions.ClientError:
            return []

    def _convert_to_url(self, summaries):
        """
        Convert the list_change_sets response from
        CloudFormation to a URL in the AWS Console.
        """
        new_summaries = []

        for summary in summaries:
            stack_id = summary["StackId"]
            change_set_id = summary["ChangeSetId"]

            region = self.stack.region
            encoded = urllib.parse.urlencode(
                {"stackId": stack_id, "changeSetId": change_set_id}
            )

            new_summaries.append(
                f"https://{region}.console.aws.amazon.com/cloudformation/home?"
                f"region={region}#/stacks/changesets/changes?{encoded}"
            )

        return new_summaries

    def generate(self):
        """
        Returns the Template for the Stack. An alias for
        dump_template for historical reasons.
        """
        return self.dump_template()

    @add_stack_hooks
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
            kwargs=self.stack.template.get_boto_call_parameter(),
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
            {"ParameterKey": key, "ParameterValue": value}
            for key, value in self.stack.parameters.items()
        ]

        kwargs = self.stack.template.get_boto_call_parameter()
        kwargs.update({"Parameters": parameters})

        response = self.connection_manager.call(
            service="cloudformation", command="estimate_template_cost", kwargs=kwargs
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
            formatted_parameters.append({"ParameterKey": name, "ParameterValue": value})

        return formatted_parameters

    def _get_role_arn(self):
        """
        Returns the Role ARN assumed by CloudFormation when building a Stack.

        Returns an empty dict if no Role is to be assumed.

        :returns: The a Role ARN
        :rtype: dict
        """
        if self.stack.cloudformation_service_role:
            return {"RoleARN": self.stack.cloudformation_service_role}
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
            return {"TimeoutInMinutes": self.stack.stack_timeout}
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

    def _wait_for_completion(
        self, timeout=0, boto_response: Optional[dict] = None
    ) -> StackStatus:
        """
        Waits for a Stack operation to finish. Prints CloudFormation events
        while it waits.

        :param timeout: Timeout before returning, in minutes.
        :param boto_response: Response from the boto call which initiated the stack change.

        :returns: The final Stack status.
        """
        timeout = 60 * timeout

        def timed_out(elapsed):
            return elapsed >= timeout if timeout else False

        status = StackStatus.IN_PROGRESS

        most_recent_event_datetime = extract_datetime_from_aws_response_headers(
            boto_response
        ) or (datetime.now(tzutc()) - timedelta(seconds=3))

        elapsed = 0
        while status == StackStatus.IN_PROGRESS and not timed_out(elapsed):
            status = self._get_simplified_status(self._get_status())
            most_recent_event_datetime = self._log_new_events(
                most_recent_event_datetime
            )
            time.sleep(4)
            elapsed += 4

        return status

    def _get_status(self):
        try:
            status = self.describe()["Stacks"][0]["StackStatus"]
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
            raise UnknownStackStatusError("{0} is unknown".format(status))

    def _log_new_events(self, after_datetime: datetime) -> datetime:
        """
        Log the latest Stack events while the Stack is being built.

        :param after_datetime: Only events after this datetime will be logged.
        :returns: The datetime of the last logged event or after_datetime if no events were logged.
        """
        events = self.describe_events()["StackEvents"]
        events.reverse()
        new_events = [event for event in events if event["Timestamp"] > after_datetime]
        for event in new_events:
            stack_event_status = [
                self.stack.name,
                event["LogicalResourceId"],
                event["ResourceType"],
                event["ResourceStatus"],
                event.get("ResourceStatusReason", ""),
            ]
            if "HookStatus" in event:
                stack_event_status.extend(
                    [
                        event["HookType"],
                        event["HookStatus"],
                        event.get("HookStatusReason", ""),
                        event["HookFailureMode"],
                    ]
                )
            self.logger.info(" ".join(stack_event_status))
            after_datetime = event["Timestamp"]
        return after_datetime

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
        cs_reason = cs_description.get("StatusReason")
        cs_exec_status = cs_description["ExecutionStatus"]
        possible_statuses = [
            "CREATE_PENDING",
            "CREATE_IN_PROGRESS",
            "CREATE_COMPLETE",
            "DELETE_COMPLETE",
            "FAILED",
        ]
        possible_execution_statuses = [
            "UNAVAILABLE",
            "AVAILABLE",
            "EXECUTE_IN_PROGRESS",
            "EXECUTE_COMPLETE",
            "EXECUTE_FAILED",
            "OBSOLETE",
        ]

        if cs_status not in possible_statuses:
            raise UnknownStackChangeSetStatusError(
                "Status {0} is unknown".format(cs_status)
            )
        if cs_exec_status not in possible_execution_statuses:
            raise UnknownStackChangeSetStatusError(
                "ExecutionStatus {0} is unknown".format(cs_status)
            )

        if cs_status == "CREATE_COMPLETE" and cs_exec_status == "AVAILABLE":
            return StackChangeSetStatus.READY
        elif cs_status in [
            "CREATE_PENDING",
            "CREATE_IN_PROGRESS",
            "CREATE_COMPLETE",
        ] and cs_exec_status in ["UNAVAILABLE", "AVAILABLE"]:
            return StackChangeSetStatus.PENDING
        elif (
            cs_status == "FAILED"
            and cs_reason is not None
            and self._change_set_creation_failed_due_to_no_changes(cs_reason)
        ):
            return StackChangeSetStatus.NO_CHANGES
        elif cs_status in ["DELETE_COMPLETE", "FAILED"] or cs_exec_status in [
            "EXECUTE_IN_PROGRESS",
            "EXECUTE_COMPLETE",
            "EXECUTE_FAILED",
            "OBSOLETE",
        ]:
            return StackChangeSetStatus.DEFUNCT
        else:  # pragma: no cover
            raise Exception("This else should not be reachable.")

    def fetch_remote_template(self) -> Optional[str]:
        """
        Returns the Template for the remote Stack

        :returns: the template body.
        """
        self.logger.debug(f"{self.stack.name} - Fetching remote template")

        original_template = self._fetch_original_template_stage()

        if isinstance(original_template, dict):
            # While not documented behavior, boto3 will attempt to deserialize the TemplateBody
            # with json.loads and return the template as a dict if it is successful; otherwise (such
            # as in when the template is in yaml, it will return the string. Therefore, we need to
            # dump the template to json if we get a dict.
            original_template = json.dumps(original_template, indent=4)

        return original_template

    def _fetch_original_template_stage(self) -> Optional[Union[str, dict]]:
        try:
            response = self.connection_manager.call(
                service="cloudformation",
                command="get_template",
                kwargs={
                    "StackName": self.stack.external_name,
                    "TemplateStage": "Original",
                },
            )
            return response["TemplateBody"]
            # Sometimes boto returns a string, sometimes a dictionary
        except botocore.exceptions.ClientError as e:
            # AWS returns a ValidationError if the stack doesn't exist
            if e.response["Error"]["Code"] == "ValidationError":
                return None
            raise

    def fetch_remote_template_summary(self):
        return self._get_template_summary(StackName=self.stack.external_name)

    def fetch_local_template_summary(self):
        boto_call_parameter = self.stack.template.get_boto_call_parameter()
        return self._get_template_summary(**boto_call_parameter)

    def _get_template_summary(self, **kwargs) -> Optional[dict]:
        try:
            template_summary = self.connection_manager.call(
                service="cloudformation", command="get_template_summary", kwargs=kwargs
            )
            return template_summary
        except botocore.exceptions.ClientError as e:
            error_response = e.response["Error"]
            if (
                error_response["Code"] == "ValidationError"
                and "does not exist" in error_response["Message"]
            ):
                return None
            raise

    @add_stack_hooks
    def diff(self, stack_differ: "StackDiffer") -> "StackDiff":
        """
        Returns a diff of local and deployed template and stack configuration using a specific diff
        library.

        :param stack_differ: The differ to use
        :returns: A StackDiff object with the full, computed diff
        """
        return stack_differ.diff(self)

    @add_stack_hooks
    def drift_detect(self) -> Dict[str, str]:
        """
        Show stack drift for a running stack.

        :returns: The stack drift detection status.
            If the stack does not exist, we return a detection and
            stack drift status of STACK_DOES_NOT_EXIST.
            If drift detection times out after 5 minutes, we return
            TIMED_OUT.
        """
        try:
            self._get_status()
        except StackDoesNotExistError:
            self.logger.info(f"{self.stack.name} - Does not exist.")
            return {
                "DetectionStatus": "STACK_DOES_NOT_EXIST",
                "StackDriftStatus": "STACK_DOES_NOT_EXIST",
            }

        response = self._detect_stack_drift()
        detection_id = response["StackDriftDetectionId"]

        try:
            response = self._wait_for_drift_status(detection_id)
        except TimeoutError as exc:
            self.logger.info(f"{self.stack.name} - {exc}")
            response = {"DetectionStatus": "TIMED_OUT", "StackDriftStatus": "TIMED_OUT"}

        return response

    @add_stack_hooks
    def drift_show(self, drifted: bool = False) -> Tuple[str, dict]:
        """
        Detect drift status on stacks.

        :param drifted: Filter out IN_SYNC resources.
        :returns: The detection status and resource drifts.
        """
        response = self.drift_detect()
        detection_status = response["DetectionStatus"]

        if detection_status in ["DETECTION_COMPLETE", "DETECTION_FAILED"]:
            response = self._describe_stack_resource_drifts()
        elif detection_status in ["TIMED_OUT", "STACK_DOES_NOT_EXIST"]:
            response = {"StackResourceDriftStatus": detection_status}
        else:
            raise Exception("Not expected to be reachable")

        response = self._filter_drifts(response, drifted)
        return (detection_status, response)

    def _wait_for_drift_status(self, detection_id: str) -> dict:
        """
        Waits for drift detection to complete.

        :param detection_id: The drift detection ID.
        :returns: The response from describe_stack_drift_detection_status.
        """
        timeout = 300
        sleep_interval = 10
        elapsed = 0

        while True:
            if elapsed >= timeout:
                raise TimeoutError(f"Timed out after {elapsed} seconds")

            self.logger.info(f"{self.stack.name} - Waiting for drift detection")
            response = self._describe_stack_drift_detection_status(detection_id)
            detection_status = response["DetectionStatus"]

            self._log_drift_status(response)

            if detection_status == "DETECTION_IN_PROGRESS":
                time.sleep(sleep_interval)
                elapsed += sleep_interval
            else:
                return response

    def _log_drift_status(self, response: dict) -> None:
        """
        Log the drift status while waiting for
        drift detection to complete.
        """
        keys = [
            "StackDriftDetectionId",
            "DetectionStatus",
            "DetectionStatusReason",
            "StackDriftStatus",
        ]

        for key in keys:
            if key in response:
                self.logger.debug(f"{self.stack.name} - {key} - {response[key]}")

    def _detect_stack_drift(self) -> dict:
        self.logger.info(f"{self.stack.name} - Detecting Stack Drift")

        return self.connection_manager.call(
            service="cloudformation",
            command="detect_stack_drift",
            kwargs={"StackName": self.stack.external_name},
        )

    def _describe_stack_drift_detection_status(self, detection_id: str) -> dict:
        self.logger.info(f"{self.stack.name} - Describing Stack Drift Detection Status")

        return self.connection_manager.call(
            service="cloudformation",
            command="describe_stack_drift_detection_status",
            kwargs={"StackDriftDetectionId": detection_id},
        )

    def _describe_stack_resource_drifts(self) -> dict:
        """
        Detects stack resource_drifts for a running stack.
        """
        self.logger.info(f"{self.stack.name} - Describing Stack Resource Drifts")

        return self.connection_manager.call(
            service="cloudformation",
            command="describe_stack_resource_drifts",
            kwargs={"StackName": self.stack.external_name},
        )

    def _filter_drifts(self, response: dict, drifted: bool) -> dict:
        """
        The filtered response after filtering out StackResourceDriftStatus.
        :param drifted: Filter out IN_SYNC resources from CLI --drifted.
        """
        if "StackResourceDrifts" not in response:
            return response

        result = {"StackResourceDrifts": []}
        include_all_drift_statuses = not drifted

        for drift in response["StackResourceDrifts"]:
            is_drifted = drift["StackResourceDriftStatus"] != "IN_SYNC"
            if include_all_drift_statuses or is_drifted:
                result["StackResourceDrifts"].append(drift)

        return result

    @add_stack_hooks
    def dump_config(self):
        """
        Dump the config for a stack.
        """
        return self.stack.config

    @add_stack_hooks_with_aliases([generate.__name__])
    def dump_template(self):
        """
        Dump the template for the Stack. An alias for generate
        for historical reasons.
        """
        return self.stack.template.body
