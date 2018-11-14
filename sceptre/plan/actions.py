# -*- coding: utf-8 -*-

"""
sceptre.plan.actions

This module implements the actions a Stack or Stack Group can take.

"""

import logging
import time
import threading
import traceback

from os import path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, wait

import botocore
from dateutil.tz import tzutc

from sceptre.config.graph import StackDependencyGraph
from sceptre.connection_manager import ConnectionManager
from sceptre.helpers import recurse_into_sub_stack_groups
from sceptre.helpers import recurse_sub_stack_groups_with_graph
from sceptre.helpers import generate_dependencies
from sceptre.helpers import generate_stack_groups
from sceptre.hooks import add_stack_hooks
from sceptre.stack_status import StackStatus
from sceptre.stack_status import StackChangeSetStatus

from sceptre.exceptions import CannotUpdateFailedStackError
from sceptre.exceptions import UnknownStackStatusError
from sceptre.exceptions import UnknownStackChangeSetStatusError
from sceptre.exceptions import StackDoesNotExistError
from sceptre.exceptions import ProtectedStackError


class StackGroupActions(object):

    def __init__(self, stack_group):
        self.logger = logging.getLogger(__name__)
        self.stack_group = stack_group

    def launch(self):
        """
        Creates or updates all stacks in the stack_group.

        :returns: dict
        """
        self.logger.debug("Launching stack_group '%s'", self.path)
        launch_dependencies = self._get_launch_dependencies()
        threading_events = self._get_threading_events()
        stack_statuses = self._get_initial_statuses()
        self.sub_stack_groups = self._get_sub_stack_groups()
        self._build(
            "launch", threading_events, stack_statuses, launch_dependencies
        )

        return stack_statuses

    def delete(self):
        """
        Deletes all stacks in the stack_group.

        :returns: dict
        """
        self.logger.debug("Deleting stack_group '%s'", self.path)
        threading_events = self._get_threading_events()
        stack_statuses = self._get_initial_statuses()
        delete_dependencies = self._get_delete_dependencies()

        self._build(
            "delete", threading_events, stack_statuses, delete_dependencies
        )
        return stack_statuses

    @recurse_into_sub_stack_groups
    def describe(self, stack_group):
        """
        Returns each stack's status.

        :returns: The stack status of each stack, keyed by the stack's name.
        :rtype: dict
        """
        response = {}
        for stack in self.stacks:
            try:
                status = stack.get_status()
            except StackDoesNotExistError:
                status = "PENDING"
            response.update({stack.name: status})
        return response

    @recurse_into_sub_stack_groups
    def describe_resources(self, stack_group):
        """
        Describes the resources of each stack in the stack_group.

        :returns: A description of each stack's resources, keyed by the stack's
            name.
        :rtype: dict
        """
        response = {}
        for stack in self.stacks:
            try:
                resources = stack.describe_resources()
                response.update({stack.name: resources})
            except(botocore.exceptions.ClientError) as exp:
                if exp.response["Error"]["Message"].endswith("does not exist"):
                    pass
                else:
                    raise
        return response

    @recurse_sub_stack_groups_with_graph
    def _build(self, command, threading_events,
               stack_statuses, dependencies, stack_group):
        """
        Launches or deletes all stacks in the stack_group.

        Whether the stack is launched or delete depends on the value of
        <command>. It does this by calling stack.<command>() for
        each stack in the stack_group. Stack.<command>() is blocking,
        because it waits for the stack to be built, so each command is run on a
        separate thread. As some stacks need to be built before others,
        depending on their depedencies, threading.Events() are used to notify
        the other stacks when a particular stack is done building.

        :param command: The stack command to run. Can be (launch | delete).
        :type command: str
        """
        if self.stacks:
            with ThreadPoolExecutor(max_workers=len(self.stacks))\
                    as stack_group:
                futures = [
                    stack_group.submit(
                        self._manage_stack_build, stack,
                        command, threading_events, stack_statuses,
                        dependencies.longest_path()
                    )
                    for stack in self.stacks
                ]
                wait(futures)
        else:
            self.logger.info(
                "No stacks found for stack_group: '%s'", self.path
            )

    def _manage_stack_build(
            self, stack, command, threading_events,
            stack_statuses, dependencies
    ):
        """
        Manages the launch or deletion of a stack.

        Waits for any stacks that ``stack`` depends on to complete, runs
        ``stack.command()``, and then marks ``stack`` as complete. If a
        dependency stack has failed, ``stack`` is marked as failed.

        :param stack: The stack to build.
        :type: sceptre.Stack
        :param threading_events: A dict of threading.Events, keyed by stack \
        names, which is used to notify other stacks when a particular stack \
        has been built.
        :type events: dict
        :param command: The stack command to run. Can be either "launch" or \
        "delete".
        :type command: str
        """
        import ipdb
        ipdb.set_trace()
        try:
            for dependency in dependencies:
                if dependency in threading_events:
                    threading_events[dependency].wait()
                    if stack_statuses[dependency] != StackStatus.COMPLETE:
                        self.logger.debug(
                            "%s, which %s depends is not complete. Marking "
                            "%s as failed.", dependency, stack, dependency
                        )
                        stack_statuses[stack.name] = StackStatus.FAILED

            if stack_statuses[stack.name] != StackStatus.FAILED:
                try:
                    status = getattr(stack, command)()
                    stack_statuses[stack.name] = status
                except Exception:
                    stack_statuses[stack.name] = StackStatus.FAILED
                    self.logger.exception(
                        "Stack %s failed to %s", stack.name, command
                    )

            threading_events[stack.name].set()
        except Exception as e:
            print(e)
            traceback.print_exc()

    def _get_threading_events(self):
        """
        Returns a threading.Event() for each stack in every sub-stack.

        :returns: A threading.Event object for each stack, keyed by the
            stack's name.
        :rtype: dict
        """
        import ipdb
        ipdb.set_trace()
        dependencies = self._get_launch_dependencies().as_dict().keys()
        stacks = []
        for keys in dependencies:
            for values in dependencies:
                stacks.append(values)

        events = {
            stack: threading.Event()
            for stack in stacks
        }
        self.logger.debug(events)
        return events

    def _get_initial_statuses(self):
        """
        Returns a "pending" sceptre.stack_status.StackStatus for each stack
        in every sub-stack.

        :returns: A "pending" stack status for each stack, keyed by the
            stack's name.
        :rtype: dict
        """
        dependencies = self._get_launch_dependencies().as_dict().keys()
        stacks = []
        for keys in dependencies:
            for values in dependencies:
                stacks.append(values)

        return {
            stack: StackStatus.PENDING
            for stack in stacks
        }

    def _get_launch_dependencies(self):
        """
        Returns a StackDependencyGraph of each stack's launch dependencies.

        :returns: A list of the stacks that a particular stack depends on
            while launching, keyed by that stack's name.
        :rtype: StackDependencyGraph
        """
        dependencies = generate_dependencies(self.stack_group)
        graph = StackDependencyGraph(dependencies)
        graph.write()
        return graph

    def _get_delete_dependencies(self):
        """
        Returns a dict of each stack's delete dependencies.

        :returns: A list of the stacks that a particular stack depends on
            while deleting, keyed by that stack's name.
        :rtype: dict
        """
        return self._get_launch_dependencies().reverse_graph()

    def _get_sub_stack_groups(self):
        stack_groups = generate_stack_groups(self.path)
        print(stack_groups)
        return stack_groups


class StackActions(object):
    """
    StackActions stores the operations a Stack can take, such as creating or
    deleting the stack.

    :param name: stack
    :type Stack: object
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
        Creates the stack.

        :returns: The stack's status.
        :rtype: sceptre.stack_status.StackStatus
        """
        self._protect_execution()
        self.logger.info("%s - Creating stack", self.stack.name)
        create_stack_kwargs = {
            "StackName": self.stack.external_name,
            "Parameters": self._format_parameters(self.stack.parameters),
            "Capabilities": ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
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
        response = self.connection_manager.call(
            service="cloudformation",
            command="create_stack",
            kwargs=create_stack_kwargs
        )
        self.logger.debug(
            "%s - Create stack response: %s", self.stack.name, response
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
        self.logger.info("%s - Updating stack", self.stack.name)
        update_stack_kwargs = {
            "StackName": self.stack.external_name,
            "Parameters": self._format_parameters(self.stack.parameters),
            "Capabilities": ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
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
            "%s - Update stack response: %s", self.stack.name, response
        )

        status = self._wait_for_completion(self.stack.stack_timeout)
        # Cancel update after timeout
        if status == StackStatus.IN_PROGRESS:
            status = self.cancel_stack_update()

        return status

    def cancel_stack_update(self):
        """
        Cancels a stack update.

        :returns: The cancelled stack status.
        :rtype: sceptre.stack_status.StackStatus
        """
        self.logger.warning(
            "%s - Update stack time exceeded the specified timeout",
            self.stack.name
        )
        response = self.connection_manager.call(
            service="cloudformation",
            command="cancel_update_stack",
            kwargs={"StackName": self.stack.external_name}
        )
        self.logger.debug(
            "%s - Cancel update stack response: %s", self.stack.name, response
        )
        return self._wait_for_completion()

    def launch(self):
        """
        Launches the stack.

        If the stack status is create_failed or rollback_complete, the
        stack is deleted. Launch then tries to create or update the stack,
        depending if it already exists. If there are no updates to be
        performed, launch exits gracefully.

        :returns: The stack's status.
        :rtype: sceptre.stack_status.StackStatus
        """
        self._protect_execution()
        self.logger.info("%s - Launching stack", self.stack.name)
        try:
            existing_status = self.get_status()
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
            status = status
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
        Deletes the stack.

        :returns: The stack's status.
        :rtype: sceptre.stack_status.StackStatus
        """
        self._protect_execution()
        self.logger.info("%s - Deleting stack", self.stack.name)
        try:
            status = self.get_status()
        except StackDoesNotExistError:
            self.logger.info("%s does not exist.", self.stack.name)
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
        Locks the stack by applying a deny all updates stack policy.
        """
        policy_path = path.join(
            # need to get to the base install path. __file__ will take us into
            # sceptre/actions so need to walk up the path.
            path.abspath(path.join(__file__, "../..")),
            "stack_policies/lock.json"
        )
        self.set_policy(policy_path)
        self.logger.info("%s - Successfully locked stack", self.stack.name)

    def unlock(self):
        """
        Unlocks the stack by applying an allow all updates stack policy.
        """
        policy_path = path.join(
            # need to get to the base install path. __file__ will take us into
            # sceptre/actions so need to walk up the path.
            path.abspath(path.join(__file__, "../..")),
            "stack_policies/unlock.json"
        )
        self.set_policy(policy_path)
        self.logger.info("%s - Successfully unlocked stack", self.stack.name)

    def describe(self):
        """
        Returns the a description of the stack.

        :returns: A stack description.
        :rtype: dict
        """
        return self.connection_manager.call(
            service="cloudformation",
            command="describe_stacks",
            kwargs={"StackName": self.stack.external_name}
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
            kwargs={"StackName": self.stack.external_name}
        )

    def describe_resources(self):
        """
        Returns the logical and physical resource IDs of the stack's resources.

        :returns: Information about the stack's resources.
        :rtype: dict
        """
        self.logger.debug("%s - Describing stack resources", self.stack.name)
        response = self.connection_manager.call(
            service="cloudformation",
            command="describe_stack_resources",
            kwargs={"StackName": self.stack.external_name}
        )
        self.logger.debug(
            "%s - Describe stack resource response: %s",
            self.stack.name,
            response
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
        self.logger.debug("%s - Describing stack outputs", self.stack.name)
        response = self.describe()

        return response["Stacks"][0].get("Outputs", [])

    def continue_update_rollback(self):
        """
        Rolls back a stack in the UPDATE_ROLLBACK_FAILED state to
        UPDATE_ROLLBACK_COMPLETE.
        """
        self.logger.debug("%s - Continuing update rollback", self.stack.name)
        continue_update_rollback_kwargs = \
            {
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
        Applies a stack policy.

        :param policy_path: the path of json file containing a aws policy
        :type policy_path: str
        """
        with open(policy_path) as f:
            policy = f.read()

        self.logger.debug(
            "%s - Setting stack policy: \n%s",
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
        self.logger.info("%s - Successfully set stack policy", self.stack.name)

    def get_policy(self):
        """
        Returns a stack's policy.

        :returns: The stack's stack policy.
        :rtype: str
        """
        self.logger.debug("%s - Getting stack policy", self.stack.name)
        response = self.connection_manager.call(
            service="cloudformation",
            command="get_stack_policy",
            kwargs={
                "StackName": self.stack.external_name
            }
        )

        return response

    def create_change_set(self, change_set_name):
        """
        Creates a change set with the name ``change_set_name``.

        :param change_set_name: The name of the change set.
        :type change_set_name: str
        """
        create_change_set_kwargs = {
            "StackName": self.stack.external_name,
            "Parameters": self._format_parameters(self.stack.parameters),
            "Capabilities": ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
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
            "%s - Creating change set '%s'", self.stack.name, change_set_name
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
            self.stack.name, change_set_name
        )

    def delete_change_set(self, change_set_name):
        """
        Deletes the change set ``change_set_name``.

        :param change_set_name: The name of the change set.
        :type change_set_name: str
        """
        self.logger.debug(
            "%s - Deleting change set '%s'", self.stack.name, change_set_name
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
        # successfully deleted the change set.
        self.logger.info(
            "%s - Successfully deleted change set '%s'",
            self.stack.name, change_set_name
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
            "%s - Describing change set '%s'", self.stack.name, change_set_name
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
        Executes the change set ``change_set_name``.

        :param change_set_name: The name of the change set.
        :type change_set_name: str
        """
        self._protect_execution()
        self.logger.debug(
            "%s - Executing change set '%s'", self.stack.name, change_set_name
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
        Lists the stack's change sets.

        :returns: The stack's change sets.
        :rtype: dict
        """
        self.logger.debug("%s - Listing change sets", self.stack.name)
        return self.connection_manager.call(
            service="cloudformation",
            command="list_change_sets",
            kwargs={
                "StackName": self.stack.external_name
            }
        )

    def generate(self):
        """
        Returns a generated template for a given Stack
        """
        return self.stack.template.body

    def validate(self):
        """
        Validates the stack's CloudFormation template.

        Raises an error if the template is invalid.

        :returns: Information about the template.
        :rtype: dict
        :raises: botocore.exceptions.ClientError
        """
        self.logger.debug("%s - Validating template", self.stack.name)
        response = self.connection_manager.call(
            service="cloudformation",
            command="validate_template",
            kwargs=self.stack.template.get_boto_call_parameter()
        )
        self.logger.debug(
            "%s - Validate template response: %s", self.stack.name, response
        )
        return response

    def estimate_cost(self):
        """
        Estimates a stack's cost.

        :returns: An estimate of the stack's cost.
        :rtype: dict
        :raises: botocore.exceptions.ClientError
        """
        self.logger.debug("%s - Estimating template cost", self.stack.name)
        response = self.connection_manager.call(
            service="cloudformation",
            command="estimate_template_cost",
            kwargs=self.stack.template.get_boto_call_parameter()
        )
        self.logger.debug(
            "%s - Estimate stack cost response: %s", self.stack.name, response
        )
        return response

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

    def _get_role_arn(self):
        """
        Returns the role arn assumed by CloudFormation when building a stack.

        Returns an empty dict if no role is to be assumed.

        :returns: the a role arn
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
        Return the timeout before considering the stack to be failing.

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
        This error is meant to stop the

        :raises: sceptre.exceptions.ProtectedStackError
        """
        if self.stack.protected:
            raise ProtectedStackError(
                "Cannot perform action on '{0}': stack protection is "
                "currently enabled".format(self.stack.name)
            )

    def _wait_for_completion(self, timeout=0):
        """
        Waits for a stack operation to finish. Prints CloudFormation events
        while it waits.

        :param timeout: Timeout before returning, in minutes.

        :returns: The final stack status.
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
            status = self._get_simplified_status(self.get_status())
            self._log_new_events()
            time.sleep(4)
            elapsed += 4

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
                self.stack.name,
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
