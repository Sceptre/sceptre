# -*- coding: utf-8 -*-

"""
sceptre.stack_group

This module implements the StackGroup class, which stores data and logic
to represent a logical grouping of stacks as a stack_group.

"""

import logging
import threading
import botocore

from concurrent.futures import ThreadPoolExecutor, wait

from .exceptions import StackDoesNotExistError

from .helpers import (recurse_into_sub_stack_groups,
                      recurse_sub_stack_groups_with_graph)
from .stack_status import StackStatus
from .config.graph import StackDependencyGraph


class StackGroup(object):
    """
    StackGroup stores information about the current stack_group.

    It implements methods for carrying out stack_group-level operations.

    Two types of StackGroups exist, non-leaf and leaf. Non-leaf
    stack_groups contain sub-stack_groups, while leaf
    stack_groups contain stacks. If a command is executed by a leaf
    stack_group, it should execute that command on the stacks it
    contains. If a command is executed by a non-leaf stack_group, it
    should invoke that command on each of its sub-stack_groups. This is
    done using the ``sceptre.helpers.recurse_into_sub_stack_groups``
    decorator.

    :param path: The name of the stack_group.
    :type path: str
    :param options: A dict of key-value pairs to update self.config with.
    :type debug: dict
    """

    def __init__(self, path, options=None):
        self.logger = logging.getLogger(__name__)
        self.path = path

        self.stacks = []
        self.sub_stack_groups = []

        self._options = {} if options is None else options

    def __repr__(self):
        return (
            "sceptre.stack_group.StackGroup("
            "path=\'{path}\', options=\'{options}\'"
            ")".format(path=self.path, options={})
        )

    def launch(self):
        """
        Creates or updates all stacks in the stack_group.

        :returns: dict
        """
        self.logger.debug("Launching stack_group '%s'", self.path)
        launch_dependencies = self._get_launch_dependencies()
        threading_events = self._get_threading_events()
        stack_statuses = self._get_initial_statuses()
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
    def describe(self):
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
    def describe_resources(self):
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
    def _build(self, command, threading_events, stack_statuses, dependencies):
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
                        dependencies
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
        for dependency in dependencies.as_dict()[stack.name]:
            if dependency in threading_events:
                threading_events[dependency].wait()
                if stack_statuses[dependency] != StackStatus.COMPLETE:
                    self.logger.debug(
                        "%s, which %s depends is not complete. Marking "
                        "%s as failed.", dependency, stack.name, dependency
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

    @recurse_into_sub_stack_groups
    def _get_threading_events(self):
        """
        Returns a threading.Event() for each stack in every sub-stack.

        :returns: A threading.Event object for each stack, keyed by the
            stack's name.
        :rtype: dict
        """
        events = {
            stack.name: threading.Event()
            for stack in self.stacks
        }
        self.logger.debug(events)
        return events

    @recurse_into_sub_stack_groups
    def _get_initial_statuses(self):
        """
        Returns a "pending" sceptre.stack_status.StackStatus for each stack
        in every sub-stack.

        :returns: A "pending" stack status for each stack, keyed by the
            stack's name.
        :rtype: dict
        """
        return {
            stack.name: StackStatus.PENDING
            for stack in self.stacks
        }

    @recurse_sub_stack_groups_with_graph
    def _get_launch_dependencies(self):
        """
        Returns a StackDependencyGraph of each stack's launch dependencies.

        :returns: A list of the stacks that a particular stack depends on
            while launching, keyed by that stack's name.
        :rtype: StackDependencyGraph
        """
        all_dependencies = {
            stack.name: stack.dependencies
            for stack in self.stacks
        }
        return StackDependencyGraph(all_dependencies)

    def _get_delete_dependencies(self):
        """
        Returns a dict of each stack's delete dependencies.

        :returns: A list of the stacks that a particular stack depends on
            while deleting, keyed by that stack's name.
        :rtype: dict
        """
        return self._get_launch_dependencies().reverse_graph()
