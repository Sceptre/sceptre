# -*- coding: utf-8 -*-

"""
sceptre.plan.plan

This module implements a SceptrePlan, which is responsible for holding all
nessessary information for a command to execute.
"""
import functools
import itertools

from os import path, walk
from typing import Dict, List, Set, Callable, Iterable, Optional
from deprecation import deprecated

from sceptre.config.graph import StackGraph
from sceptre.config.reader import ConfigReader
from sceptre.context import SceptreContext
from sceptre.diffing.stack_differ import StackDiff
from sceptre.exceptions import ConfigFileNotFoundError
from sceptre.helpers import sceptreise_path
from sceptre.plan.executor import SceptrePlanExecutor
from sceptre.stack import Stack
from sceptre import __version__


def require_resolved(func) -> Callable:
    @functools.wraps(func)
    def wrapped(self: "SceptrePlan", *args, **kwargs):
        if self.launch_order is None:
            raise RuntimeError(f"You cannot call {func.__name__}() before resolve().")
        return func(self, *args, **kwargs)

    return wrapped


class SceptrePlan(object):
    def __init__(self, context: SceptreContext):
        """
        Intialises a SceptrePlan and generates the Stacks, StackGraph and
        launch order of required.

        :param context: A SceptreContext
        """
        self.context = context
        self.command = None
        self.reverse = None
        self.launch_order: Optional[List[Set[Stack]]] = None

        self.config_reader = ConfigReader(context)
        all_stacks, command_stacks = self.config_reader.construct_stacks()
        self.graph = StackGraph(all_stacks)
        self.command_stacks = command_stacks

    @require_resolved
    def _execute(self, *args):
        executor = SceptrePlanExecutor(self.command, self.launch_order)
        return executor.execute(*args)

    def _generate_launch_order(self, reverse=False) -> List[Set[Stack]]:
        if self.context.ignore_dependencies:
            return [self.command_stacks]

        graph = self.graph.filtered(self.command_stacks, reverse)

        launch_order = []
        while graph.graph:
            batch = set()
            for stack in graph:
                if graph.count_dependencies(stack) == 0:
                    batch.add(stack)
            launch_order.append(batch)

            for stack in batch:
                graph.remove_stack(stack)

        if not launch_order:
            raise ConfigFileNotFoundError(
                "No stacks detected from the given path '{}'. Valid stack paths are: {}".format(
                    sceptreise_path(self.context.command_path),
                    self._valid_stack_paths(),
                )
            )

        return launch_order

    @require_resolved
    def __iter__(self) -> Iterable[Stack]:
        """Iterates the stacks in the launch_order"""
        # We cast it to list so it's "frozen" in time, in case the launch order is modified
        # while iterating.
        yield from list(itertools.chain.from_iterable(self.launch_order))

    @require_resolved
    def remove_stack_from_plan(self, stack: Stack):
        for batch in self.launch_order:
            if stack in batch:
                batch.remove(stack)
                return

    @require_resolved
    def filter(self, predicate: Callable[[Stack], bool]):
        """Filters the plan's resolved launch_order to remove specific stacks.

        :param predicate: This callable should take a single Stack and return True if it should stay
            in the launch_order or False if it should be filtered out.
        """
        for stack in self:
            if not predicate(stack):
                self.remove_stack_from_plan(stack)

    def resolve(self, command, reverse=False):
        if command == self.command and reverse == self.reverse:
            return

        self.command = command
        self.reverse = reverse
        self.launch_order = self._generate_launch_order(reverse)

    def template(self, *args):
        """
        Returns the CloudFormation Template used to create the Stack.

        :returns: A dictionary of Stacks and their templates.
        :rtype: dict
        """
        self.resolve(command=self.template.__name__)
        return self._execute(*args)

    def create(self, *args):
        """
        Creates the Stack.

        :returns: A dictionary of Stacks and their status.
        :rtype: dict
        """
        self.resolve(command=self.create.__name__)
        return self._execute(*args)

    def update(self, *args):
        """
        Updates the Stack.

        :returns: A dictionary of Stacks and their status.
        :rtype: dict
        """
        self.resolve(command=self.update.__name__)
        return self._execute(*args)

    def cancel_stack_update(self, *args):
        """
        Cancels a Stack update.

        :returns: A dictionary of Stacks and their cancelled statuses.
        :rtype: dict
        """
        self.resolve(command=self.cancel_stack_update.__name__)
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
        self.resolve(command=self.launch.__name__)
        return self._execute(*args)

    def delete(self, *args):
        """
        Deletes the Stack.

        :returns: A dictionary of Stacks and their status.
        :rtype: dict
        """
        self.resolve(command=self.delete.__name__, reverse=True)
        return self._execute(*args)

    def lock(self, *args):
        """
        Locks the Stack by applying a deny all updates Stack policy.

        :returns: A dictionary of Stacks
        :rtype: dict
        """
        self.resolve(command=self.lock.__name__)
        return self._execute(*args)

    def unlock(self, *args):
        """
        Unlocks the Stack by applying an allow all updates Stack policy.

        :returns: A dictionary of Stacks
        :rtype: dict
        """
        self.resolve(command=self.unlock.__name__)
        return self._execute(*args)

    def describe(self, *args):
        """
        Returns the a description of the Stack.

        :returns: A dictionary of Stacks and their description.
        :rtype: dict
        """
        self.resolve(command=self.describe.__name__)
        return self._execute(*args)

    def describe_events(self, *args):
        """
        Returns a dictionary contianing the Stack events.

        :returns: A dictionary of Stacks and their CloudFormation events.
        :rtype: dict
        """
        self.resolve(command=self.describe_events.__name__)
        return self._execute(*args)

    def describe_resources(self, *args):
        """
        Returns the logical and physical resource IDs of the Stack's resources.

        :returns: A dictionary of Stacks and their resources.
        :rtype: dict
        """
        self.resolve(command=self.describe_resources.__name__)
        return self._execute(*args)

    def describe_outputs(self, *args):
        """
        Returns a list of Stack outputs.

        :returns: A dictionary of Stacks and their outputs.
        :rtype: dict
        """
        self.resolve(command=self.describe_outputs.__name__)
        return self._execute(*args)

    def continue_update_rollback(self, *args):
        """
        Rolls back a Stack in the UPDATE_ROLLBACK_FAILED state to
        UPDATE_ROLLBACK_COMPLETE.

        :returns: A dictionary of Stacks
        :rtype: dict
        """
        self.resolve(command=self.continue_update_rollback.__name__)
        return self._execute(*args)

    def set_policy(self, *args):
        """
        Applies a Stack policy.

        :param policy_path: the path of json file containing a aws policy
        :type policy_path: str
        :returns: A dictionary of Stacks
        :rtype: dict
        """
        self.resolve(command=self.set_policy.__name__)
        return self._execute(*args)

    def get_policy(self, *args):
        """
        Returns a Stack's policy.

        :returns: A dictionary of Stacks and their Stack policy.
        :rtype: dict
        """
        self.resolve(command=self.get_policy.__name__)
        return self._execute(*args)

    def create_change_set(self, *args):
        """
        Creates a Change Set with the name ``change_set_name``.

        :param change_set_name: The name of the Change Set.
        :type change_set_name: str
        :returns: A dictionary of Stacks
        :rtype: dict
        """
        self.resolve(command=self.create_change_set.__name__)
        return self._execute(*args)

    def delete_change_set(self, *args):
        """
        Deletes the Change Set ``change_set_name``.

        :param change_set_name: The name of the Change Set.
        :type change_set_name: str
        :returns: A dictionary of Stacks
        :rtype: dict
        """
        self.resolve(command=self.delete_change_set.__name__)
        return self._execute(*args)

    def describe_change_set(self, *args):
        """
        Describes the Change Set ``change_set_name``.

        :param change_set_name: The name of the Change Set.
        :type change_set_name: str
        :returns: A dictionary of Stacks and their Change Set description.
        :rtype: dict
        """
        self.resolve(command=self.describe_change_set.__name__)
        return self._execute(*args)

    def execute_change_set(self, *args):
        """
        Executes the Change Set ``change_set_name``.

        :param change_set_name: The name of the Change Set.
        :type change_set_name: str
        :returns: A dictionary of Stacks and their status.
        :rtype: dict
        """
        self.resolve(command=self.execute_change_set.__name__)
        return self._execute(*args)

    def list_change_sets(self, *args):
        """
        Lists the Stack's Change Sets.

        :returns: TA dictionary of Stacks and their Change Sets.
        :rtype: dict
        """
        self.resolve(command=self.list_change_sets.__name__)
        return self._execute(*args)

    def get_status(self, *args):
        """
        Returns the Stack's status.

        :returns: A dictionary of Stacks and their status.
        :rtype: dict
        :raises: sceptre.exceptions.StackDoesNotExistError
        """
        self.resolve(command=self.get_status.__name__)
        return self._execute(*args)

    def wait_for_cs_completion(self, *args):
        """
        Waits while the Stack Change Set status is "pending".

        :param change_set_name: The name of the Change Set.
        :type change_set_name: str
        :rtype: dict
        :rtype: sceptre.stack_status.StackChangeSetStatus
        """
        self.resolve(command=self.wait_for_cs_completion.__name__)
        return self._execute(*args)

    def validate(self, *args):
        """
        Validates the Stack's CloudFormation template.

        Raises an error if the Template is invalid.

        :returns: A dictionary of Stacks and their template validation information.
        :rtype: dict
        :raises: botocore.exceptions.ClientError
        """
        self.resolve(command=self.validate.__name__)
        return self._execute(*args)

    def estimate_cost(self, *args):
        """
        Estimates a Stack's cost.

        :returns: A dictionary of Stacks and their estimated costs.
        :rtype: dict
        :raises: botocore.exceptions.ClientError
        """
        self.resolve(command=self.estimate_cost.__name__)
        return self._execute(*args)

    @deprecated("4.2.0", "5.0.0", __version__, "Use dump template instead.")
    def generate(self, *args):
        """
        Returns a generated Template for a given Stack

        :returns: A dictionary of Stacks and their template body.
        :rtype: dict
        """
        self.resolve(command=self.generate.__name__)
        return self._execute(*args)

    def _valid_stack_paths(self):
        return [
            sceptreise_path(
                path.relpath(path.join(dirpath, f), self.context.config_path)
            )
            for dirpath, dirnames, files in walk(self.context.config_path)
            for f in files
            if not f.endswith(self.context.config_file)
        ]

    def fetch_remote_template(self, *args):
        """
        Returns a generated Template for a given Stack

        :returns: A list of Stacks and their template body.
        :rtype: List[str]
        """
        self.resolve(command=self.fetch_remote_template.__name__)
        return self._execute(*args)

    def diff(self, *args) -> Dict[Stack, StackDiff]:
        """
        Show diffs between the running and generated stack.

        :returns: A dict where the keys are Stack objects and the values are StackDiffs.
        """
        self.resolve(command=self.diff.__name__)
        return self._execute(*args)

    def drift_detect(self, *args) -> Dict[Stack, str]:
        """
        Show drift detection status of a stack.

        :returns: A list of detected drift against running stacks.
        """
        self.resolve(command=self.drift_detect.__name__)
        return self._execute(*args)

    def drift_show(self, *args) -> Dict[Stack, str]:
        """
        Show stack drift for a running stack.

        :returns: A list of detected drift against running stacks.
        """
        self.resolve(command=self.drift_show.__name__)
        return self._execute(*args)

    def dump_config(self, *args):
        """
        Dump the config for a stack.
        """
        self.resolve(command=self.dump_config.__name__)
        return self._execute(*args)

    def dump_template(self, *args):
        """
        Returns a generated Template for a given Stack
        """
        self.resolve(command=self.dump_template.__name__)
        return self._execute(*args)
