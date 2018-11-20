# -*- coding: utf-8 -*-

"""
sceptre.plan.plan

This module implements a SceptrePlan, which is responsible for holding all
nessessary information for a command to execute.
"""

from sceptre.config.graph import StackGraph
from sceptre.config.reader import ConfigReader
from sceptre.plan.executor import SceptrePlanExecutor


class SceptrePlan(object):

    def __init__(self, context):
        """
        Intialises a SceptrePlan and generates the Stacks, StackGraph and
        launch order of required.

        :param context: A SceptreContext
        :type sceptre.context.SceptreContext:
        """
        self.context = context
        self.responses = []
        config_reader = ConfigReader(context)
        stacks = config_reader.construct_stacks()
        self.graph = StackGraph(stacks)
        self.launch_order = self._generate_launch_order()

    def _execute(self, *args):
        executor = SceptrePlanExecutor(self.command, self.launch_order)
        return executor.execute(*args)

    def _execute_reverse(self, *args):
        executor = SceptrePlanExecutor(self.command,
                                       list(reversed(self.launch_order)))
        return executor.execute(*args)

    def _resolve(self, command=None):
        if command:
            self.command = command
        else:
            raise TypeError(
                "Command passed to plan.resolve() must have a value")

    def _generate_launch_order(self):
        launch_order = []
        while self.graph.graph:
            batch = set()
            for stack in self.graph:
                if self.graph.count_dependencies(stack) == 0:
                    batch.add(stack)
            launch_order.append(batch)

            for stack in batch:
                self.graph.remove_stack(stack)

        return launch_order

    def template(self, *args):
        """
        Returns the CloudFormation Template used to create the Stack.

        :returns: A dictionary of Stacks and their templates.
        :rtype: dict
        """
        self._resolve(command=self.template.__name__)
        return self._execute(*args)

    def create(self, *args):
        """
        Creates the Stack.

        :returns: A dictionary of Stacks and their status.
        :rtype: dict
        """
        self._resolve(command=self.create.__name__)
        return self._execute(*args)

    def update(self, *args):
        """
        Updates the Stack.

        :returns: A dictionary of Stacks and their status.
        :rtype: dict
        """
        self._resolve(command=self.update.__name__)
        return self._execute(*args)

    def cancel_stack_update(self, *args):
        """
        Cancels a Stack update.

        :returns: A dictionary of Stacks and their cancelled statuses.
        :rtype: dict
        """
        self._resolve(command=self.cancel_stack_update.__name__)
        return self._execute(*args)

    def launch(self, *args):
        """
        Launches the Stack.

        If the Stack status is create_failed or rollback_complete, the
        Stack is deleted. Launch then tries to create or update the Stack,
        depending if it already exists. If there are no updates to be
        performed, launch exits gracefully.

        :returns: A dictionary of Stacks and their status.
        :rtype: dict
        """
        self._resolve(command=self.launch.__name__)
        return self._execute(*args)

    def delete(self, *args):
        """
        Deletes the Stack.

        :returns: A dictionary of Stacks and their status.
        :rtype: dict
        """
        self._resolve(command=self.delete.__name__)
        return self._execute_reverse(*args)

    def lock(self, *args):
        """
        Locks the Stack by applying a deny all updates Stack policy.
        """
        self._resolve(command=self.lock.__name__)
        return self._execute(*args)

    def unlock(self, *args):
        """
        Unlocks the Stack by applying an allow all updates Stack policy.
        """
        self._resolve(command=self.unlock.__name__)
        return self._execute(*args)

    def describe(self, *args):
        """
        Returns the a description of the Stack.

        :returns: A dictionary of Stacks and their description.
        :rtype: dict
        """
        self._resolve(command=self.describe.__name__)
        return self._execute(*args)

    def describe_events(self, *args):
        """
        Returns a dictionary contianing the Stack events.

        :returns: A dictionary of Stacks and their CloudFormation events.
        :rtype: dict
        """
        self._resolve(command=self.describe_events.__name__)
        return self._execute(*args)

    def describe_resources(self, *args):
        """
        Returns the logical and physical resource IDs of the Stack's resources.

        :returns: A dictionary of Stacks and their resources.
        :rtype: dict
        """
        self._resolve(command=self.describe_resources.__name__)
        return self._execute(*args)

    def describe_outputs(self, *args):
        """
        Returns a list of Stack outputs.

        :returns: A dictionary of Stacks and their outputs.
        :rtype: dict
        """
        self._resolve(command=self.describe_outputs.__name__)
        return self._execute(*args)

    def continue_update_rollback(self, *args):
        """
        Rolls back a Stack in the UPDATE_ROLLBACK_FAILED state to
        UPDATE_ROLLBACK_COMPLETE.
       """
        self._resolve(command=self.continue_update_rollback.__name__)
        return self._execute(*args)

    def set_policy(self, *args):
        """
        Applies a Stack policy.

        :param policy_path: the path of json file containing a aws policy
        :type policy_path: str
        """
        self._resolve(command=self.set_policy.__name__)
        return self._execute(*args)

    def get_policy(self, *args):
        """
        Returns a Stack's policy.

        :returns: A dictionary of Stacks and their Stack policy.
        :rtype: str
        """
        self._resolve(command=self.get_policy.__name__)
        return self._execute(*args)

    def create_change_set(self, *args):
        """
        Creates a Change Set with the name ``change_set_name``.

        :param change_set_name: The name of the Change Set.
        :type change_set_name: str
        """
        self._resolve(command=self.create_change_set.__name__)
        return self._execute(*args)

    def delete_change_set(self, *args):
        """
        Deletes the Change Set ``change_set_name``.

        :param change_set_name: The name of the Change Set.
        :type change_set_name: str
        """
        self._resolve(command=self.delete_change_set.__name__)
        return self._execute(*args)

    def describe_change_set(self, *args):
        """
        Describes the Change Set ``change_set_name``.

        :param change_set_name: The name of the Change Set.
        :type change_set_name: str
        :returns: A dictionary of Stacks and their Change Set description.
        :rtype: dict
        """
        self._resolve(command=self.describe_change_set.__name__)
        return self._execute(*args)

    def execute_change_set(self, *args):
        """
        Executes the Change Set ``change_set_name``.

        :param change_set_name: The name of the Change Set.
        :type change_set_name: str
        """
        self._resolve(command=self.execute_change_set.__name__)
        return self._execute(*args)

    def list_change_sets(self, *args):
        """
        Lists the Stack's Change Sets.

        :returns: TA dictionary of Stacks and their Change Sets.
        :rtype: dict
        """
        self._resolve(command=self.list_change_sets.__name__)
        return self._execute(*args)

    def get_status(self, *args):
        """
        Returns the Stack's status.

        :returns: A dictionary of Stacks and their status.
        :rtype: dict
        :raises: sceptre.exceptions.StackDoesNotExistError
        """
        self._resolve(command=self.get_status.__name__)
        return self._execute(*args)

    def wait_for_cs_completion(self, *args):
        """
        Waits while the Stack Change Set status is "pending".

        :param change_set_name: The name of the Change Set.
        :type change_set_name: str
        :rtype: dict
        :rtype: sceptre.stack_status.StackChangeSetStatus
        """
        self._resolve(command=self.wait_for_cs_completion.__name__)
        return self._execute(*args)

    def validate(self, *args):
        """
        Validates the Stack's CloudFormation template.

        Raises an error if the Template is invalid.

        :returns: A dictionary of Stacks and their template validation information.
        :rtype: dict
        :raises: botocore.exceptions.ClientError
        """
        self._resolve(command=self.validate.__name__)
        return self._execute(*args)

    def estimate_cost(self, *args):
        """
        Estimates a Stack's cost.

        :returns: A dictionary of Stacks and their estimated costs.
        :rtype: dict
        :raises: botocore.exceptions.ClientError
        """
        self._resolve(command=self.estimate_cost.__name__)
        return self._execute(*args)

    def generate(self, *args):
        """
        Returns a generated Template for a given Stack
        """
        self._resolve(command=self.generate.__name__)
        return self._execute(*args)
