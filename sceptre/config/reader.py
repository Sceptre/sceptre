# -*- coding: utf-8 -*-

"""
sceptre.config

This module implements a ConfigReader class, which is responsible for reading
and constructing Stacks.
"""

import collections
import datetime
import fnmatch
import logging
from os import environ, path, walk
from pkg_resources import iter_entry_points
import yaml

import jinja2
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from sceptre import __version__
from sceptre.exceptions import InvalidConfigFileError
from sceptre.exceptions import InvalidSceptreDirectoryError
from sceptre.exceptions import VersionIncompatibleError
from sceptre.exceptions import ConfigFileNotFoundError
from sceptre.helpers import sceptreise_path
from sceptre.stack import Stack
from sceptre.config import strategies

ConfigAttributes = collections.namedtuple("Attributes", "required optional")

CONFIG_MERGE_STRATEGIES = {
    'dependencies': strategies.list_join,
    'hooks': strategies.child_wins,
    'notifications': strategies.child_wins,
    'on_failure': strategies.child_wins,
    'parameters': strategies.child_wins,
    'profile': strategies.child_wins,
    'project_code': strategies.child_wins,
    'protect': strategies.child_wins,
    'region': strategies.child_wins,
    'required_version': strategies.child_wins,
    'role_arn': strategies.child_wins,
    'sceptre_user_data': strategies.child_wins,
    'stack_name': strategies.child_wins,
    'stack_tags': strategies.child_wins,
    'stack_timeout': strategies.child_wins,
    'template_bucket_name': strategies.child_wins,
    'template_key_value': strategies.child_wins,
    'template_path': strategies.child_wins
}

STACK_GROUP_CONFIG_ATTRIBUTES = ConfigAttributes(
    {
        "project_code",
        "region"
    },
    {
        "template_bucket_name",
        "template_key_prefix",
        "required_version"
    }
)

STACK_CONFIG_ATTRIBUTES = ConfigAttributes(
    {
        "template_path"
    },
    {
        "dependencies",
        "hooks",
        "notifications",
        "on_failure",
        "parameters",
        "profile",
        "protect",
        "role_arn",
        "sceptre_user_data",
        "stack_name",
        "stack_tags",
        "stack_timeout"
    }
)

INTERNAL_CONFIG_ATTRIBUTES = ConfigAttributes(
    {
        "project_path",
        "stack_group_path",
    },
    {
    }
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
            # This function signture is required by PyYAML
            def class_constructor(loader, node):
                return node_class(
                    loader.construct_scalar(node)
                )  # pragma: no cover

            return class_constructor

        for group in entry_point_groups:
            for entry_point in iter_entry_points(group):
                # Retrieve name and class from entry point
                node_tag = u'!' + entry_point.name
                node_class = entry_point.load()

                # Add constructor to PyYAML loader
                yaml.SafeLoader.add_constructor(
                    node_tag, constructor_factory(node_class)
                )
                self.logger.debug(
                    "Added constructor for %s with node tag %s",
                    str(node_class), node_tag
                )

    def construct_stacks(self):
        """
        Traverses the files under the command path.
        For each file encountered, a Stack is constructed
        using the correct config. Dependencies are traversed
        and a final set of Stacks is returned.

        :returns: A set of Stacks.
        :rtype: set
        """
        stack_map = {}
        command_stacks = set()
        if self.context.ignore_dependencies:
            root = self.context.full_command_path()
        else:
            root = self.context.full_config_path()

        if path.isfile(root):
            todo = {root}
        else:
            todo = set()
            for directory_name, sub_directories, files in walk(root, followlinks=True):
                for filename in fnmatch.filter(files, '*.yaml'):
                    if filename.startswith('config.'):
                        continue

                    todo.add(path.join(directory_name, filename))

        stack_group_configs = {}

        while todo:
            abs_path = todo.pop()
            rel_path = path.relpath(
                abs_path, start=self.context.full_config_path())
            directory, filename = path.split(rel_path)

            if directory in stack_group_configs:
                stack_group_config = stack_group_configs[directory]
            else:
                stack_group_config = stack_group_configs[directory] = \
                    self.read(path.join(directory, self.context.config_file))

            stack = self._construct_stack(rel_path, stack_group_config)
            stack_map[sceptreise_path(rel_path)] = stack

            if abs_path.startswith(self.context.full_command_path()):
                command_stacks.add(stack)

        stacks = set()
        for stack in stack_map.values():
            if not self.context.ignore_dependencies:
                stack.dependencies = [
                    stack_map[sceptreise_path(dep)]
                    for dep in stack.dependencies
                ]
            else:
                stack.dependencies = []
            stacks.add(stack)

        return stacks, command_stacks

    def read(self, rel_path, base_config=None):
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
            "stack_group_path": directory_path
        }

        # Adding defaults from base config.
        if base_config:
            config.update(base_config)

        # Check if file exists, but ignore config.yaml as can be inherited.
        if not path.isfile(abs_path)\
                and not filename.endswith(self.context.config_file):
            raise ConfigFileNotFoundError(
                "Config file \"{0}\" not found.".format(rel_path)
            )

        # Parse and read in the config files.
        this_config = self._recursive_read(directory_path, filename, config)

        if "dependencies" in config or "dependencies" in this_config:
            this_config['dependencies'] = \
                CONFIG_MERGE_STRATEGIES['dependencies'](
                    this_config.get("dependencies"),
                    config.get("dependencies")
            )
        config.update(this_config)

        self._check_version(config)

        self.logger.debug("Config: %s", config)
        return config

    def _recursive_read(self, directory_path, filename, stack_group_config):
        """
        Traverses the directory_path, from top to bottom, reading in all
        relevant config files. If config attributes are encountered further
        down the StackGroup they are merged with the parent as defined in the
        `CONFIG_MERGE_STRATEGIES` dict.

        :param directory_path: Relative directory path to config to read.
        :type directory_path: str
        :param filename: File name for the config to read.
        :type filename: dict
        :param stack_group_config: The loaded config file for the StackGroup
        :type stack_group_config: dict
        :returns: Representation of inherited config.
        :rtype: dict
        """

        parent_directory = path.split(directory_path)[0]

        # Base condition for recursion
        config = {}

        if directory_path:
            config = self._recursive_read(parent_directory, filename, stack_group_config)

        # Read config file and overwrite inherited properties
        child_config = self._render(directory_path, filename, stack_group_config) or {}

        for config_key, strategy in CONFIG_MERGE_STRATEGIES.items():
            value = strategy(
                config.get(config_key), child_config.get(config_key)
            )

            if value:
                child_config[config_key] = value

        config.update(child_config)

        return config

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
        if path.isfile(path.join(abs_directory_path, basename)):
            jinja_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(abs_directory_path),
                undefined=jinja2.StrictUndefined
            )
            template = jinja_env.get_template(basename)
            self.templating_vars.update(stack_group_config)
            rendered_template = template.render(
                self.templating_vars,
                command_path=self.context.command_path.split(path.sep),
                environment_variable=environ
            )

            config = yaml.safe_load(rendered_template)

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
        if 'required_version' in config:
            required_version = config['required_version']
            if Version(sceptre_version) not in SpecifierSet(required_version, True):
                raise VersionIncompatibleError(
                    "Current sceptre version ({0}) does not meet version "
                    "requirements: {1}".format(
                        sceptre_version, required_version
                    )
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
        if "template_bucket_name" in config:
            template_key = "/".join([
                sceptreise_path(stack_name), "{time_stamp}.json".format(
                    time_stamp=datetime.datetime.utcnow().strftime(
                        "%Y-%m-%d-%H-%M-%S-%fZ"
                    )
                )
            ])

            bucket_region = config.get("region", None)

            if "template_key_prefix" in config:
                prefix = config["template_key_prefix"]
                template_key = "/".join([prefix.strip("/"), template_key])

            s3_details = {
                "bucket_name": config["template_bucket_name"],
                "bucket_key": template_key,
                "bucket_region": bucket_region
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
        config = self.read(rel_path, stack_group_config)
        stack_name = path.splitext(rel_path)[0]

        # Check for missing mandatory attributes
        for required_key in REQUIRED_KEYS:
            if required_key not in config:
                raise InvalidConfigFileError(
                    "Required attribute '{0}' not found in configuration of '{1}'.".format(
                        required_key, stack_name
                    )
                )

        abs_template_path = path.join(
            self.context.project_path, self.context.templates_path,
            sceptreise_path(config["template_path"])
        )

        s3_details = self._collect_s3_details(
            stack_name, config
        )
        stack = Stack(
            name=stack_name,
            project_code=config["project_code"],
            template_path=abs_template_path,
            region=config["region"],
            template_bucket_name=config.get("template_bucket_name"),
            template_key_prefix=config.get("template_key_prefix"),
            required_version=config.get("required_version"),
            profile=config.get("profile"),
            parameters=config.get("parameters", {}),
            sceptre_user_data=config.get("sceptre_user_data", {}),
            hooks=config.get("hooks", {}),
            s3_details=s3_details,
            dependencies=config.get("dependencies", []),
            role_arn=config.get("role_arn"),
            protected=config.get("protect", False),
            tags=config.get("stack_tags", {}),
            external_name=config.get("stack_name"),
            notifications=config.get("notifications"),
            on_failure=config.get("on_failure"),
            stack_timeout=config.get("stack_timeout", 0),
            stack_group_config=parsed_stack_group_config
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
            for key in
            set(stack_group_config) - set(CONFIG_MERGE_STRATEGIES)
        }
        parsed_config.pop("project_path")
        parsed_config.pop("stack_group_path")
        return parsed_config
