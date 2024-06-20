# -*- coding: utf-8 -*-

"""
sceptre.config

This module implements a ConfigReader class, which is responsible for reading
and constructing Stacks.
"""

import collections
import copy
import datetime
import fnmatch
import logging
import sys
import yaml
import json

from os import environ, path, walk
from typing import Set, Tuple
from pathlib import Path
from jinja2 import Environment
from jinja2 import StrictUndefined
from jinja2 import FileSystemLoader
from jinja2 import select_autoescape
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from sceptre import __version__
from sceptre.exceptions import SceptreException
from sceptre.exceptions import DependencyDoesNotExistError
from sceptre.exceptions import InvalidConfigFileError
from sceptre.exceptions import InvalidSceptreDirectoryError
from sceptre.exceptions import VersionIncompatibleError
from sceptre.exceptions import ConfigFileNotFoundError
from sceptre.helpers import sceptreise_path, logging_level, write_debug_file
from sceptre.stack import Stack
from sceptre.config import strategies

ConfigAttributes = collections.namedtuple("Attributes", "required optional")


CONFIG_MERGE_STRATEGY_OVERRIDES = {
    "dependencies": strategies.LIST_STRATEGIES,
    "hooks": strategies.LIST_STRATEGIES,
    "notifications": strategies.LIST_STRATEGIES,
    "parameters": strategies.DICT_STRATEGIES,
    "sceptre_user_data": strategies.DICT_STRATEGIES,
    "stack_tags": strategies.DICT_STRATEGIES,
}

CONFIG_MERGE_STRATEGIES = {
    "dependencies": strategies.list_join,
    "dependencies_inheritance": strategies.child_or_parent,
    "hooks": strategies.child_wins,
    "hooks_inheritance": strategies.child_or_parent,
    "iam_role": strategies.child_wins,
    "sceptre_role": strategies.child_wins,
    "iam_role_session_duration": strategies.child_wins,
    "sceptre_role_session_duration": strategies.child_wins,
    "notifications": strategies.child_wins,
    "notifications_inheritance": strategies.child_or_parent,
    "on_failure": strategies.child_wins,
    "parameters": strategies.child_wins,
    "parameters_inheritance": strategies.child_or_parent,
    "profile": strategies.child_wins,
    "project_code": strategies.child_wins,
    "protect": strategies.child_wins,
    "region": strategies.child_wins,
    "required_version": strategies.child_wins,
    "role_arn": strategies.child_wins,
    "cloudformation_service_role": strategies.child_wins,
    "sceptre_user_data": strategies.child_wins,
    "sceptre_user_data_inheritance": strategies.child_or_parent,
    "stack_name": strategies.child_wins,
    "stack_tags": strategies.child_wins,
    "stack_tags_inheritance": strategies.child_or_parent,
    "stack_timeout": strategies.child_wins,
    "template_bucket_name": strategies.child_wins,
    "template_key_value": strategies.child_wins,
    "template": strategies.child_wins,
    "template_path": strategies.child_wins,
    "ignore": strategies.child_wins,
    "obsolete": strategies.child_wins,
}


STACK_GROUP_CONFIG_ATTRIBUTES = ConfigAttributes(
    {"project_code", "region"},
    {
        "template_bucket_name",
        "template_key_prefix",
        "required_version",
        "j2_environment",
    },
)

STACK_CONFIG_ATTRIBUTES = ConfigAttributes(
    {},
    {
        "template_path",
        "template",
        "dependencies",
        "dependencies_inheritance",
        "hooks",
        "hooks_inheritance",
        "iam_role",
        "sceptre_role",
        "iam_role_session_duration",
        "sceptre_role_session_duration",
        "notifications",
        "on_failure",
        "parameters",
        "parameters_inheritance",
        "profile",
        "protect",
        "role_arn",
        "cloudformation_service_role",
        "sceptre_user_data",
        "sceptre_user_data_inheritance",
        "stack_name",
        "stack_tags",
        "stack_tags_inheritance",
        "stack_timeout",
    },
)

REQUIRED_KEYS = STACK_GROUP_CONFIG_ATTRIBUTES.required.union(
    STACK_CONFIG_ATTRIBUTES.required
)


class ConfigReader(object):
    """
    Parses YAML configuration files and produces Stack objects.

    Responsible for loading Resolvers and Hook classes and adding them as
    constructors to the PyYAML parser.

    :param context: A SceptreContext.
    :type sceptre.context.SceptreContext:
    """

    def __init__(self, context):
        self.logger = logging.getLogger(__name__)
        self.context = context
        self.full_config_path = self.context.full_config_path()

        # Check is valid sceptre project folder
        self._check_valid_project_path(self.full_config_path)

        # Add Resolver and Hook classes to PyYAML loader
        self._add_yaml_constructors(["sceptre.hooks", "sceptre.resolvers"])
        if not self.context.user_variables:
            self.context.user_variables = {}

        self.templating_vars = {"var": self.context.user_variables}

    @staticmethod
    def _iterate_entry_points(group):
        """
        Helper to determine whether to use pkg_resources or importlib.metadata.
        https://docs.python.org/3/library/importlib.metadata.html
        """
        if sys.version_info < (3, 10):
            from pkg_resources import iter_entry_points

            return iter_entry_points(group)
        else:
            from importlib.metadata import entry_points

            return entry_points(group=group)

    def _add_yaml_constructors(self, entry_point_groups):
        """
        Adds PyYAML constructor functions for all classes found registered at
        the given entry point groups. Classes are registered whereby the node
        tag is the entry point name.

        :param entry_point_groups: Names of entry point groups.
        :type entry_point_groups: list
        """
        self.logger.debug(
            "Adding yaml constructors for the entry point groups {0}".format(
                entry_point_groups
            )
        )

        def constructor_factory(node_class):
            """
            Returns constructor that will initialise objects from a
            given node class.

            :param node_class: Class representing the node.
            :type node_class: class
            :returns: Class initialiser.
            :rtype: func
            """

            # This function signature is required by PyYAML
            def class_constructor(loader, node):
                return node_class(
                    loader.construct_object(self.resolve_node_tag(loader, node))
                )  # pragma: no cover

            return class_constructor

        for group in entry_point_groups:
            for entry_point in self._iterate_entry_points(group):
                # Retrieve name and class from entry point
                node_tag = "!" + entry_point.name
                node_class = entry_point.load()

                # Add constructor to PyYAML loader
                yaml.SafeLoader.add_constructor(
                    node_tag, constructor_factory(node_class)
                )
                self.logger.debug(
                    "Added constructor for %s with node tag %s",
                    str(node_class),
                    node_tag,
                )

    def resolve_node_tag(self, loader, node):
        node = copy.copy(node)
        node.tag = loader.resolve(type(node), node.value, (True, False))
        return node

    def construct_stacks(self) -> Tuple[Set[Stack], Set[Stack]]:
        """
        Traverses the files under the command path.
        For each file encountered, a Stack is constructed
        using the correct config. Dependencies are traversed
        and a final set of Stacks is returned.

        :returns: A set of Stacks.
        """
        stack_map = {}
        command_stacks = set()

        root = self.context.full_command_path()

        if self.context.full_scan:
            root = self.context.full_config_path()

        if path.isfile(root):
            todo = {root}
        else:
            todo = set()
            for directory_name, sub_directories, files in walk(root, followlinks=True):
                for filename in fnmatch.filter(files, "*.yaml"):
                    if filename.startswith("config."):
                        continue

                    todo.add(path.join(directory_name, filename))

        stack_group_configs = {}
        full_todo = todo.copy()
        deps_todo = set()

        while todo:
            abs_path = todo.pop()
            rel_path = path.relpath(abs_path, start=self.context.full_config_path())
            directory, filename = path.split(rel_path)

            if directory in stack_group_configs:
                stack_group_config = stack_group_configs[directory]
            else:
                stack_group_config = stack_group_configs[directory] = self._read(
                    path.join(directory, self.context.config_file)
                )

            stack = self._construct_stack(rel_path, stack_group_config)
            for dep in stack.dependencies:
                full_dep = str(Path(self.context.full_config_path(), dep))
                if not path.exists(full_dep):
                    raise DependencyDoesNotExistError(
                        "{stackname}: Dependency {dep} not found. "
                        "Please make sure that your dependencies stack_outputs "
                        "have their full path from `config` defined.".format(
                            stackname=stack.name, dep=dep
                        )
                    )

                if full_dep not in full_todo and full_dep not in deps_todo:
                    todo.add(full_dep)
                    deps_todo.add(full_dep)

            stack_map[sceptreise_path(rel_path)] = stack

            full_command_path = self.context.full_command_path()
            if abs_path == full_command_path or abs_path.startswith(
                full_command_path.rstrip(path.sep) + path.sep
            ):
                command_stacks.add(stack)

        stacks = self.resolve_stacks(stack_map)

        return stacks, command_stacks

    def resolve_stacks(self, stack_map) -> Set[Stack]:
        """
        Transforms map of Stacks into a set of Stacks, transforms dependencies
        from a list of Strings (stack names) to a list of Stacks.

        :param stack_map: Map of stacks, containing dependencies as list of Strings.
        :type base_config: dict
        :returns: Set of stacks, containing dependencies as list of Stacks.
        :rtype: set
        :raises: sceptre.exceptions.DependencyDoesNotExistError
        """
        stacks = set()
        for stack in stack_map.values():
            if not self.context.ignore_dependencies:
                for i, dep in enumerate(stack.dependencies):
                    try:
                        if not isinstance(dep, Stack):
                            # If the dependency was inherited from a stack group, it might already
                            # have been mapped and so doesn't need to be mapped again.
                            stack.dependencies[i] = stack_map[sceptreise_path(dep)]
                    except KeyError:
                        raise DependencyDoesNotExistError(
                            "{stackname}: Dependency {dep} not found. "
                            "Valid dependency names are: "
                            "{stackkeys}. "
                            "Please make sure that your dependencies stack_outputs "
                            "have their full path from `config` defined.".format(
                                stackname=stack.name,
                                dep=dep,
                                stackkeys=", ".join(stack_map.keys()),
                            )
                        )
                # We deduplicate the dependencies using a set here, since it's possible that a given
                # dependency ends up in the list multiple times.
                stack.dependencies = list(set(stack.dependencies))
            else:
                stack.dependencies = []
            stacks.add(stack)
        return stacks

    def _read(self, rel_path, base_config=None):
        """
        Reads in configuration from one or more YAML files
        within the Sceptre project folder.

        :param rel_path: Relative path to config to read.
        :type rel_path: str
        :param base_config: Base config to provide defaults.
        :type base_config: dict
        :returns: Config read from config files.
        :rtype: dict
        """
        self.logger.debug("Reading in '%s' files...", rel_path)
        directory_path, filename = path.split(rel_path)
        abs_path = path.join(self.full_config_path, rel_path)

        # Adding properties from class
        config = {
            "project_path": self.context.project_path,
            "stack_group_path": directory_path,
        }

        # Adding defaults from base config.
        if base_config:
            config.update(base_config)

        # Check if file exists, but ignore config.yaml as can be inherited.
        if not path.isfile(abs_path) and not filename.endswith(
            self.context.config_file
        ):
            raise ConfigFileNotFoundError(
                'Config file "{0}" not found.'.format(rel_path)
            )

        # Parse and read in the config files.
        this_config = self._recursive_read(directory_path, filename, config)
        # Apply merge strategies with the config that includes base_config values.
        this_config.update(self._get_merge_with_stratgies(config, this_config))
        config.update(this_config)

        self._check_version(config)

        self.logger.debug("Config: %s", config)
        return config

    def _recursive_read(
        self, directory_path: str, filename: str, stack_group_config: dict
    ) -> dict:
        """
        Traverses the directory_path, from top to bottom, reading in all
        relevant config files. If config attributes are encountered further
        down the StackGroup they are merged with the parent as defined in the
        `CONFIG_MERGE_STRATEGIES` dict.

        :param directory_path: Relative directory path to config to read.
        :param filename: File name for the config to read.
        :param stack_group_config: The loaded config file for the StackGroup
        :returns: Representation of inherited config.
        """

        parent_directory = path.split(directory_path)[0]

        # Base condition for recursion
        config = {}

        if directory_path:
            config = self._recursive_read(
                parent_directory, filename, stack_group_config
            )

        # Combine the stack_group_config with the nested config dict
        config_group = stack_group_config.copy()
        config_group.update(config)

        # Read config file and overwrite inherited properties
        child_config = self._render(directory_path, filename, config_group) or {}
        child_config.update(self._get_merge_with_stratgies(config, child_config))
        config.update(child_config)
        return config

    def _get_merge_with_stratgies(self, left: dict, right: dict) -> dict:
        """
        Returns a new dict with only the merge values of the two inputs, using the
        merge strategies defined for each key.
        """
        merge = {}

        # Then apply the merge strategies to each item
        for config_key, default_strategy in CONFIG_MERGE_STRATEGIES.items():
            strategy = default_strategy
            override_key = f"{config_key}_inheritance"
            if override_key in CONFIG_MERGE_STRATEGIES:
                name = CONFIG_MERGE_STRATEGIES[override_key](
                    left.get(override_key), right.get(override_key)
                )
                if not name:
                    pass
                elif name not in CONFIG_MERGE_STRATEGY_OVERRIDES[config_key]:
                    raise SceptreException(
                        f"{name} is not a valid inheritance strategy for {config_key}"
                    )
                else:
                    strategy = CONFIG_MERGE_STRATEGY_OVERRIDES[config_key][name]

            value = strategy(left.get(config_key), right.get(config_key))
            if value:
                merge[config_key] = value

        return merge

    def _render(self, directory_path, basename, stack_group_config):
        """
        Reads a configuration file, loads the config file as a template
        and returns config loaded from the file.

        :param directory_path: Relative directory path to config to read.
        :type directory_path: str
        :param basename: The filename of the config file
        :type basename: str
        :param stack_group_config: The loaded config file for the StackGroup
        :type stack_group_config: dict
        :returns: rendered template of config file.
        :rtype: dict
        """
        config = {}
        abs_directory_path = path.join(self.full_config_path, directory_path)

        if not path.isfile(path.join(abs_directory_path, basename)):
            return

        default_j2_environment_config = {
            "autoescape": select_autoescape(
                disabled_extensions=("yaml",),
                default=True,
            ),
            "loader": FileSystemLoader(abs_directory_path),
            "undefined": StrictUndefined,
        }
        j2_environment_config = strategies.dict_merge(
            default_j2_environment_config,
            stack_group_config.get("j2_environment", {}),
        )
        j2_environment = Environment(**j2_environment_config)

        try:
            template = j2_environment.get_template(basename)
        except Exception as err:
            raise SceptreException(
                f"{Path(directory_path, basename).as_posix()} - {err}"
            ) from err

        # Reset the template cache to avoid leakage between StackGroups (#937)
        template_vars = {"var": self.templating_vars["var"]}
        if "stack_group_config" in self.templating_vars:
            template_vars["stack_group_config"] = self.templating_vars[
                "stack_group_config"
            ]
        self.templating_vars = template_vars

        self.templating_vars.update(stack_group_config)

        try:
            rendered_template = template.render(
                self.templating_vars,
                command_path=self.context.command_path.split(path.sep),
                environment_variable=environ,
            )
        except Exception as err:
            message = f"{Path(directory_path, basename).as_posix()} - {err}"

            if logging_level() == logging.DEBUG:
                debug_file_path = write_debug_file(
                    json.dumps(self.templating_vars, indent=4), prefix="vars_"
                )
                message += f"\nTemplating vars saved to: {debug_file_path}"

            raise SceptreException(message) from err

        try:
            config = yaml.safe_load(rendered_template)
        except Exception as err:
            message = f"Error parsing {abs_directory_path}{basename}:\n{err}"

            if logging_level() == logging.DEBUG:
                debug_file_path = write_debug_file(
                    rendered_template, prefix="rendered_"
                )
                message += f"\nRendered template saved to: {debug_file_path}"

            raise ValueError(message)

        return config

    @staticmethod
    def _check_valid_project_path(config_path):
        """
        Raises an InvalidSceptreDirectoryError if ``path`` is not a directory.

        :param path: A config directory path.
        :type path: str
        :raises: sceptre.exceptions.InvalidSceptreDirectoryError
        """
        if not path.isdir(config_path):
            raise InvalidSceptreDirectoryError(
                "Check '{0}' exists.".format(config_path)
            )

    def _check_version(self, config):
        """
        Raises a VersionIncompatibleException when the current Sceptre version
        does not comply with the configured version requirement.

        :raises: sceptre.exceptions.VersionIncompatibleException
        """
        sceptre_version = __version__
        if "required_version" in config:
            required_version = config["required_version"]
            if Version(sceptre_version) not in SpecifierSet(required_version, True):
                raise VersionIncompatibleError(
                    "Current sceptre version ({0}) does not meet version "
                    "requirements: {1}".format(sceptre_version, required_version)
                )

    @staticmethod
    def _collect_s3_details(stack_name, config):
        """
        Collects and constructs details for where to store the Template in S3.

        :param stack_name: Stack name.
        :type stack_name: str
        :param config: Config with details.
        :type config: dict
        :returns: S3 details.
        :rtype: dict
        """
        s3_details = None
        # If the config explicitly sets the template_bucket_name to None, we don't want to enter
        # this conditional block.
        if config.get("template_bucket_name") is not None:
            template_key = "/".join(
                [
                    sceptreise_path(stack_name),
                    "{time_stamp}.json".format(
                        time_stamp=datetime.datetime.utcnow().strftime(
                            "%Y-%m-%d-%H-%M-%S-%fZ"
                        )
                    ),
                ]
            )

            if "template_key_prefix" in config:
                prefix = config["template_key_prefix"]
                template_key = "/".join([prefix.strip("/"), template_key])

            s3_details = {
                "bucket_name": config["template_bucket_name"],
                "bucket_key": template_key,
            }
        return s3_details

    def _construct_stack(self, rel_path, stack_group_config=None):
        """
        Constructs an individual Stack object from a config path and a
        base config.

        :param rel_path: A relative config file path.
        :type rel_path: str
        :param stack_group_config: The Stack group config to use as defaults.
        :type stack_group_config: dict
        :returns: Stack object
        :rtype: sceptre.stack.Stack
        """

        directory, filename = path.split(rel_path)
        if filename == self.context.config_file:
            pass

        self.templating_vars["stack_group_config"] = stack_group_config
        parsed_stack_group_config = self._parsed_stack_group_config(stack_group_config)
        config = self._read(rel_path, stack_group_config)
        stack_name = path.splitext(rel_path)[0]

        # Check for missing mandatory attributes
        for required_key in REQUIRED_KEYS:
            if required_key not in config:
                raise InvalidConfigFileError(
                    "Required attribute '{0}' not found in configuration of '{1}'.".format(
                        required_key, stack_name
                    )
                )

        s3_details = self._collect_s3_details(stack_name, config)
        # If disable/enable rollback was specified on the command line, use that. Otherwise,
        # fall back to the stack config.
        disable_rollback = self.context.command_params.get("disable_rollback")
        if disable_rollback is None:
            disable_rollback = config.get("disable_rollback", False)

        stack = Stack(
            name=stack_name,
            project_code=config["project_code"],
            template_path=config.get("template_path"),
            template_handler_config=config.get("template"),
            region=config["region"],
            template_bucket_name=config.get("template_bucket_name"),
            template_key_prefix=config.get("template_key_prefix"),
            required_version=config.get("required_version"),
            sceptre_role=config.get("sceptre_role"),
            iam_role=config.get("iam_role"),
            sceptre_role_session_duration=config.get("sceptre_role_session_duration"),
            iam_role_session_duration=config.get("iam_role_session_duration"),
            profile=config.get("profile"),
            parameters=config.get("parameters", {}),
            sceptre_user_data=config.get("sceptre_user_data", {}),
            hooks=config.get("hooks", {}),
            s3_details=s3_details,
            dependencies=config.get("dependencies", []),
            role_arn=config.get("role_arn"),
            cloudformation_service_role=config.get("cloudformation_service_role"),
            protected=config.get("protect", False),
            tags=config.get("stack_tags", {}),
            external_name=config.get("stack_name"),
            notifications=config.get("notifications"),
            on_failure=config.get("on_failure"),
            disable_rollback=disable_rollback,
            stack_timeout=config.get("stack_timeout", 0),
            ignore=config.get("ignore", False),
            obsolete=config.get("obsolete", False),
            stack_group_config=parsed_stack_group_config,
            config=config,
        )

        del self.templating_vars["stack_group_config"]
        return stack

    def _parsed_stack_group_config(self, stack_group_config):
        """
        Remove all config items that are supported by Sceptre and
        remove the `project_path` and `stack_group_path` added by `read()`.
        Return a dictionary that has only user-specified config items.
        """
        parsed_config = {
            key: stack_group_config[key]
            for key in set(stack_group_config) - set(CONFIG_MERGE_STRATEGIES)
        }
        parsed_config.pop("stack_group_path")
        return parsed_config
