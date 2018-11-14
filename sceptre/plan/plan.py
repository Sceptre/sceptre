# -*- coding: utf-8 -*-

"""
sceptre.plan.executor
This module implements a SceptrePlanExecutor, which is responsible for
executing the command specified in a SceptrePlan.
"""

import fnmatch
import jinja2
import yaml
from os import environ, path, walk

from sceptre.config.graph import StackDependencyGraph
from sceptre.stack_group import StackGroup
from sceptre.config.reader import ConfigReader
from sceptre.plan.executor import SceptrePlanExecutor


class SceptrePlan(SceptrePlanExecutor):

    def __init__(self, context):
        self.context = context
        self.stack_group = self._generate_stack_group()
        self.responses = []
        self.errors = []
        self.dependencies = StackDependencyGraph(self._generate_dependencies())
        self.launch_order = self._generate_launch_order()

    def _execute(self, *args):
        return super(SceptrePlan, self).execute(self, *args)

    def _resolve(self, command=None):
        if command:
            self.command = command
        else:
            raise TypeError(
                "Command passed to plan.resolve() must have a value")

    def _generate_stack_group(self):
        """
        Parses the path to generate relevant Stack Group and Stack object.

        :returns: return StackGroup
        :rtype: StackGroup
        """
        config_reader = ConfigReader(self.context)

        if path.splitext(self.context.command_path)[1]:
            stack_group = StackGroup(self.context.command_path)
            stack = config_reader.construct_stack(self.context.command_path)
            stack_group.stacks.append(stack)
            return stack_group
        else:
            stack_group = config_reader.construct_stack_group(
                self.context.command_path)
            return stack_group

    def _generate_dependencies(self):
        final_deps = {}
        templating_vars = {}
        stack_group = self.stack_group
        import ipdb
        ipdb.set_trace()

        def recurse_deps(stack_group):
            stack_group = stack_group
            root = path.join(self.context.full_config_path(), stack_group.path)

            for directory_name, sub_directories, files in walk(root):
                for filename in fnmatch.filter(files, '*.yaml'):
                    if not filename.startswith("config"):
                        def get_dependencies(config_path):
                            abs_directory_path = path.abspath(directory_name)
                            if path.isfile(path.join(abs_directory_path, filename)):
                                stack_group = jinja2.Environment(
                                    loader=jinja2.FileSystemLoader(
                                        abs_directory_path),
                                    undefined=jinja2.StrictUndefined
                                )

                                template = stack_group.get_template(filename)
                                rendered_template = template.render(
                                    environment_variable=environ,
                                    stack_group_path=config_path,
                                    **templating_vars
                                )

                                config = yaml.safe_load(rendered_template)
                                return config.get("dependencies", [])

                        dependencies = get_dependencies(directory_name)
                        stack_list = []
                        for d in dependencies:
                            cr = ConfigReader(self.context)
                            stack = cr.construct_stack(d)
                            stack_list.append(stack)

                        config_reader = ConfigReader(self.context)
                        stack = config_reader.construct_stack(
                            self._get_stack_group_name(
                                directory_name) + '/' + filename
                        )

                        final_deps.update({stack: stack_list})

                        for d in dependencies:
                            config_reader = ConfigReader(self.context)
                            sg = config_reader.construct_stack_group(
                                path.split(d)[0])
                            recurse_deps(sg)

        recurse_deps(stack_group)
        return final_deps

    def _get_stack_group_name(self, abs_path):
        temp_path = abs_path
        final_path = ""

        while path.split(temp_path)[1] != 'config':
            final_path = path.join(path.split(temp_path)[1], final_path)
            temp_path = path.split(temp_path)[0]

        return final_path[:-1]  # remove trailing slash

    def _generate_launch_order(self):
        launch_order = [self.dependencies.longest_path()]
        # For each node with no incoming edges
        # Generate the longest path from that node
        # Add that longest path as a list into launch_order[]
        # if node has no incoming or outgoing edges add to a "singles" list
        # once complete append singles list to launch_order[]
        return launch_order

    def template(self, *args):
        """
        Returns the CloudFormation template used to create the stack.

        :returns: The stack's template.
        :rtype: str
        """
        self._resolve(command=self.template.__name__)
        self._execute(*args)

    def create(self, *args):
        """
        Creates the stack.

        :returns: The stack's status.
        :rtype: sceptre.stack_status.StackStatus
        """
        self._resolve(command=self.create.__name__)
        self._execute(*args)

    def update(self, *args):
        """
        Updates the stack.

        :returns: The stack's status.
        :rtype: sceptre.stack_status.StackStatus
        """
        self._resolve(command=self.update.__name__)
        self._execute(*args)

    def cancel_stack_update(self, *args):
        """
        Cancels a stack update.

        :returns: The cancelled stack status.
        :rtype: sceptre.stack_status.StackStatus
        """
        self._resolve(command=self.cancel_stack_update.__name__)
        self._execute(*args)

    def launch(self, *args):
        """
        Launches the stack.

        If the stack status is create_failed or rollback_complete, the
        stack is deleted. Launch then tries to create or update the stack,
        depending if it already exists. If there are no updates to be
        performed, launch exits gracefully.

        :returns: The stack's status.
        :rtype: sceptre.stack_status.StackStatus
        """
        self._resolve(command=self.launch.__name__)
        self._execute(*args)

    def delete(self, *args):
        """
        Deletes the stack.

        :returns: The stack's status.
        :rtype: sceptre.stack_status.StackStatus
        """
        self._resolve(command=self.delete.__name__)
        self._execute(*args)

    def lock(self, *args):
        """
        Locks the stack by applying a deny all updates stack policy.
        """
        self._resolve(command=self.lock.__name__)
        self._execute(*args)

    def unlock(self, *args):
        """
        Unlocks the stack by applying an allow all updates stack policy.
        """
        self._resolve(command=self.unlock.__name__)
        self._execute(*args)

    def describe(self, *args):
        """
        Returns the a description of the stack.

        :returns: A stack description.
        :rtype: dict
        """
        self._resolve(command=self.describe.__name__)
        self._execute(*args)

    def describe_events(self, *args):
        """
        Returns a dictionary contianing the stack events.

        :returns: The CloudFormation events for a stack.
        :rtype: dict
        """
        self._resolve(command=self.describe_events.__name__)
        self._execute(*args)

    def describe_resources(self, *args):
        """
        Returns the logical and physical resource IDs of the stack's resources.

        :returns: Information about the stack's resources.
        :rtype: dict
        """
        self._resolve(command=self.describe_resources.__name__)
        self._execute(*args)

    def describe_outputs(self, *args):
        """
        Returns a list of stack outputs.

        :returns: The stack's outputs.
        :rtype: list
        """
        self._resolve(command=self.describe_outputs.__name__)
        self._execute(*args)

    def continue_update_rollback(self, *args):
        """
        Rolls back a stack in the UPDATE_ROLLBACK_FAILED state to
        UPDATE_ROLLBACK_COMPLETE.
       """
        self._resolve(command=self.continue_update_rollback.__name__)
        self._execute(*args)

    def set_policy(self, *args):
        """
        Applies a stack policy.

        :param policy_path: the path of json file containing a aws policy
        :type policy_path: str
        """
        self._resolve(command=self.set_policy.__name__)
        self._execute(*args)

    def get_policy(self, *args):
        """
        Returns a stack's policy.

        :returns: The stack's stack policy.
        :rtype: str
        """
        self._resolve(command=self.get_policy.__name__)
        self._execute(*args)

    def create_change_set(self, *args):
        """
        Creates a change set with the name ``change_set_name``.

        :param change_set_name: The name of the change set.
        :type change_set_name: str
        """
        self._resolve(command=self.create_change_set.__name__)
        self._execute(*args)

    def delete_change_set(self, *args):
        """
        Deletes the change set ``change_set_name``.

        :param change_set_name: The name of the change set.
        :type change_set_name: str
        """
        self._resolve(command=self.delete_change_set.__name__)
        self._execute(*args)

    def describe_change_set(self, *args):
        """
        Describes the change set ``change_set_name``.

        :param change_set_name: The name of the change set.
        :type change_set_name: str
        :returns: The description of the change set.
        :rtype: dict
        """
        self._resolve(command=self.describe_change_set.__name__)
        self._execute(*args)

    def execute_change_set(self, *args):
        """
        Executes the change set ``change_set_name``.

        :param change_set_name: The name of the change set.
        :type change_set_name: str
        """
        self._resolve(command=self.execute_change_set.__name__)
        self._execute(*args)

    def list_change_sets(self, *args):
        """
        Lists the stack's change sets.

        :returns: The stack's change sets.
        :rtype: dict
        """
        self._resolve(command=self.list_change_sets.__name__)
        self._execute(*args)

    def get_status(self, *args):
        """
        Returns the stack's status.

        :returns: The stack's status.
        :rtype: sceptre.stack_status.StackStatus
        :raises: sceptre.exceptions.StackDoesNotExistError
        """
        self._resolve(command=self.get_status.__name__)
        self._execute(*args)

    def wait_for_cs_completion(self, *args):
        """
        Waits while the stack change set status is "pending".

        :param change_set_name: The name of the change set.
        :type change_set_name: str
        :returns: The change set's status.
        :rtype: sceptre.stack_status.StackChangeSetStatus
        """
        self._resolve(command=self.wait_for_cs_completion.__name__)
        self._execute(*args)

    def validate(self, *args):
        """
        Validates the stack's CloudFormation template.

        Raises an error if the template is invalid.

        :returns: Information about the template.
        :rtype: dict
        :raises: botocore.exceptions.ClientError
        """
        self._resolve(command=self.validate.__name__)
        self._execute(*args)

    def estimate_cost(self, *args):
        """
        Estimates a stack's cost.

        :returns: An estimate of the stack's cost.
        :rtype: dict
        :raises: botocore.exceptions.ClientError
        """
        self._resolve(command=self.estimate_cost.__name__)
        self._execute(*args)

    def generate(self, *args):
        """
        Returns a generated template for a given Stack
        """
        self._resolve(command=self.generate.__name__)
        self._execute(*args)
