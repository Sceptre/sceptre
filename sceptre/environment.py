# -*- coding: utf-8 -*-

"""
sceptre.environment

This module implements the Environment class, which stores data and logic to
represent a logical grouping of stacks as an environment.

"""

from glob import glob
import logging
import os
import threading

import botocore

from concurrent.futures import ThreadPoolExecutor, wait

from .exceptions import CircularDependenciesError
from .exceptions import StackDoesNotExistError

from .config import Config
from .connection_manager import ConnectionManager
from .exceptions import InvalidEnvironmentPathError
from .helpers import recurse_into_sub_environments, get_name_tuple
from .stack import Stack
from .stack_status import StackStatus


class Environment(object):
    """
    Environment stores information about the current environment.

    It implements methods for carrying out environment-level operations.

    Two types of Environments exist, non-leaf and leaf. Non-leaf environments
    contain sub-environments, while leaf environments contain stacks. If a
    command is executed by a leaf environment, it should execute that command
    on the stacks it contains. If a command is executed by a non-leaf
    environment, it should invoke that command on each of its sub-environments.
    This is done using the
    ``sceptre.helpers.recurse_into_sub_environments`` decorator.

    :param sceptre_dir: The absolute path to the Sceptre directory.
    :type project dir: str
    :param environment_path: The name of the environment.
    :type environment_path: str
    :param options: A dict of key-value pairs to update self.config with.
    :type debug: dict
    """
    def __init__(self, sceptre_dir, environment_path, options=None):
        self.logger = logging.getLogger(__name__)

        self.sceptre_dir = sceptre_dir
        self.path = self._validate_path(environment_path)
        self._options = {} if options is None else options

        self._is_leaf = None

        if self.is_leaf:
            self.stacks = self._load_stacks()
        else:
            self.environments = self._load_environments()

    def __repr__(self):
        return (
            "sceptre.environment.Environment(sceptre_dir='{0}', "
            "environment_path='{1}', options={2})".format(
                self.sceptre_dir, self.path, self._options
            )
        )

    @staticmethod
    def _validate_path(path):
        """
        Normalises backslashes to forward slashes for non-unix systems.
        Raises an InvalidEnvironmentPathError if the path has a leading or
        trailing slash.

        :param path: A directory path
        :type path: str
        :raises: sceptre.exceptions.InvalidEnvironmentPathError
        :returns: A normalised path with forward slashes.
        :rtype: string
        """
        path = path.replace("\\", "/")
        if path.endswith("/") or path.startswith("/"):
            raise InvalidEnvironmentPathError(
                "'{0}' is an invalid path string. Environment paths should "
                "not have leading or trailing slashes.".format(path)
            )
        return path

    @property
    def is_leaf(self):
        """
        Returns a boolean indicating if this environment is a leaf environment.

        The environment is a leaf environment if all items in the environent's
        directory are files (i.e. there are no sub-environments).

        :returns: A boolean indicating whether the environment is a leaf
            environment or not.
        :returns: bool
        """
        if self._is_leaf is None:
            self._is_leaf = all([
                os.path.isfile(path)
                for path in glob(os.path.join(
                    self.sceptre_dir, "config", self.path, "*"
                ))
            ])
        return self._is_leaf

    def launch(self):
        """
        Creates or updates all stacks in the environment.

        :returns: dict
        """
        self.logger.debug("Launching environment '%s'", self.path)
        threading_events = self._get_threading_events()
        stack_statuses = self._get_initial_statuses()
        launch_dependencies = self._get_launch_dependencies(self.path)

        self._check_for_circular_dependencies(launch_dependencies)
        self._build(
            "launch", threading_events, stack_statuses, launch_dependencies
        )
        return stack_statuses

    def delete(self):
        """
        Deletes all stacks in the environment.

        :returns: dict
        """
        self.logger.debug("Deleting environment '%s'", self.path)
        threading_events = self._get_threading_events()
        stack_statuses = self._get_initial_statuses()
        delete_dependencies = self._get_delete_dependencies()

        self._check_for_circular_dependencies(delete_dependencies)
        self._build(
            "delete", threading_events, stack_statuses, delete_dependencies
        )
        return stack_statuses

    @recurse_into_sub_environments
    def describe(self):
        """
        Returns each stack's status.

        :returns: The stack status of each stack, keyed by the stack's name.
        :rtype: dict
        """
        response = {}
        for stack in self.stacks.values():
            try:
                status = stack.get_status()
            except StackDoesNotExistError:
                status = "PENDING"
            response.update({stack.name: status})
        return response

    @recurse_into_sub_environments
    def describe_resources(self):
        """
        Describes the resources of each stack in the environment.

        :returns: A description of each stack's resources, keyed by the stack's
            name.
        :rtype: dict
        """
        response = {}
        for stack in self.stacks.values():
            try:
                resources = stack.describe_resources()
                response.update({stack.name: resources})
            except(botocore.exceptions.ClientError) as exp:
                if exp.response["Error"]["Message"].endswith("does not exist"):
                    pass
                else:
                    raise
        return response

    @recurse_into_sub_environments
    def _build(self, command, threading_events, stack_statuses, dependencies):
        """
        Launches or deletes all stacks in the environment.

        Whether the stack is launched or delete depends on the value of
        <command>. It does this by calling stack.<command>() for
        each stack in the environment. Stack.<command>() is blocking, because
        it waits for the stack to be built, so each command is run on a
        separate thread. As some stacks need to be built before others,
        depending on their depedencies, threading.Events() are used to notify
        the other stacks when a particular stack is done building.

        :param command: The stack command to run. Can be (launch | delete).
        :type command: str
        """
        num_stacks = len(self.stacks)
        with ThreadPoolExecutor(max_workers=num_stacks) as executor:
            futures = [
                executor.submit(
                    self._manage_stack_build, stack,
                    command, threading_events, stack_statuses, dependencies
                )
                for stack in self.stacks.values()
            ]
            wait(futures)

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
        for dependency in dependencies[stack.name]:
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

    @recurse_into_sub_environments
    def _get_threading_events(self):
        """
        Returns a threading.Event() for each stack in every sub-environment.

        :returns: A threading.Event object for each stack, keyed by the
            stack's name.
        :rtype: dict
        """
        return {
            stack.name: threading.Event()
            for stack in self.stacks.values()
        }

    @recurse_into_sub_environments
    def _get_initial_statuses(self):
        """
        Returns a "pending" sceptre.stack_status.StackStatus for each stack
        in every sub-environment.

        :returns: A "pending" stack status for each stack, keyed by the
            stack's name.
        :rtype: dict
        """
        return {
            stack.name: StackStatus.PENDING
            for stack in self.stacks.values()
        }

    @recurse_into_sub_environments
    def _get_launch_dependencies(self, top_level_environment_path):
        """
        Returns a dict of each stack's launch dependencies.

        :returns: A list of the stacks that a particular stack depends on
            while launching, keyed by that stack's name.
        :rtype: dict
        """
        all_dependencies = {
            stack.name: stack.dependencies
            for stack in self.stacks.values()
        }

        # Filter out dependencies which aren't under the top level environmnent
        launch_dependencies = {
            stack_name: [
                dependency
                for dependency in dependencies
                if dependency.startswith(top_level_environment_path)
            ]
            for stack_name, dependencies in all_dependencies.items()
        }
        return launch_dependencies

    def _get_delete_dependencies(self):
        """
        Returns a dict of each stack's delete dependencies.

        :returns: A list of the stacks that a particular stack depends on
            while deleting, keyed by that stack's name.
        :rtype: dict
        """
        launch_dependencies = self._get_launch_dependencies(self.path)
        delete_dependencies = {
            stack_name: [] for stack_name in launch_dependencies
        }
        for stack_name, dependencies in launch_dependencies.items():
            for dependency in dependencies:
                delete_dependencies[dependency].append(stack_name)
        return delete_dependencies

    def _check_for_circular_dependencies(self, dependencies):
        """
        Checks to make sure that no stacks are dependent on stacks which are
        dependent on the first stack.

        :raises: sceptre.workplan.CircularDependenciesException
        """
        self.logger.debug("Checking for circular dependencies...")
        for stack_name, stack_dependencies in dependencies.items():
            for dependency in stack_dependencies:
                if stack_name in dependencies[dependency]:
                    raise CircularDependenciesError(
                        "The {0} stack is dependent on the {1} stack, which "
                        "is in turn dependent on the {0} "
                        "stack.".format(stack_name, dependency)
                    )
        self.logger.debug("No circular dependencies found")

    def _get_config(self):
        """
        Initialises sceptre.Config and reads in the configuration data
        from each ``config.yaml`` file along the environment path. Overwrites
        the config with the values in ``self._options``.

        :returns: The environment's configuration.
        :rtype: dict
        """
        config = Config(
            sceptre_dir=self.sceptre_dir,
            environment_path=self.path,
            base_file_name="config"
        )
        config.read(self._options.get("user_variables"))
        config.update(self._options)

        return config

    def _get_available_stacks(self):
        """
        Returns all the stacks contained in the environment.

        :returns: A list of the environment's stacks.
        :rtype: list
        """
        config_files = glob(os.path.join(
            self.sceptre_dir, "config", self.path, "*.yaml"
        ))
        basenames = [
            os.path.splitext(os.path.basename(config_file))[0]
            for config_file in config_files
        ]

        if "config" in basenames:
            basenames.remove("config")

        stack_names = [
            "/".join([self.path, basename]) for basename in basenames
        ]
        return stack_names

    def _load_stacks(self):
        """
        Initialises and returns all of the environment's stacks.

        :returns: A dictionary of the stacks, keyed by the stack's name
        :rtype: dict
        """
        config = self._get_config()
        connection_manager = ConnectionManager(
            region=config["region"],
            iam_role=config.get("iam_role")
        )
        stacks = {}
        for stack_name in self._get_available_stacks():
            self.logger.debug("Initialising stack '%s'", stack_name)
            stack = Stack(
                name=stack_name,
                environment_config=config,
                connection_manager=connection_manager
            )
            stacks[get_name_tuple(stack_name)[-1]] = stack
        return stacks

    def _get_available_environments(self):
        """
        Returns all the sub-environments contained in the environment.

        :returns: A list of the environment's sub-environments.
        :rtype: list
        """
        items_in_dir = glob(os.path.join(
            self.sceptre_dir, "config", self.path, "*"
        ))
        dirs = [
            item for item in items_in_dir
            if os.path.isdir(item)
        ]
        available_environments = [
            os.path.relpath(d, os.path.join(self.sceptre_dir, "config"))
            for d in dirs
        ]
        return available_environments

    def _load_environments(self):
        """
        Initialises and returns all of the environment's sub-environments.

        :returns: A dict of sub-environments, keyed by the environment's names
        :returns: dict
        """
        environments = {}

        for environment_name in self._get_available_environments():
            self.logger.debug(
                "Initialising '%s' environment...", environment_name
            )
            environment = Environment(
                sceptre_dir=self.sceptre_dir,
                environment_path=environment_name,
                options=self._options
            )
            environments[environment_name] = environment
        return environments
