# -*- coding: utf-8 -*-

"""
sceptre.config

This module implements a Config class, which stores a stack or
stack_group's configuration.
"""

from glob import glob
import copy
import collections
import datetime
import logging
from os import path, environ
from pkg_resources import iter_entry_points
import yaml

import jinja2
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from . import __version__
from .exceptions import InvalidSceptreDirectoryError, ConfigFileNotFoundError
from .exceptions import StackGroupNotFoundError, VersionIncompatibleError
from .stack_group import StackGroup
from .stack import Stack

ConfigAttributes = collections.namedtuple("Attributes", "required optional")

STACK_GROUP_CONFIG_ATTRIBUTES = ConfigAttributes(
    {
        "project_code",
        "region"
    },
    {
        "template_bucket_name",
        "template_key_prefix",
        "require_version"
    }
)

STACK_CONFIG_ATTRIBUTES = ConfigAttributes(
    {
        "template_path"
    },
    {
        "profile",
        "dependencies",
        "hooks",
        "parameters",
        "protect",
        "sceptre_user_data",
        "stack_name",
        "stack_tags",
        "role_arn",
        "stack_timeout"
    }
)


class ConfigReader(object):
    """
    Respresents a Sceptre project folder. Reads in yaml configuration files and
    produces Stack or StackGroup objects. Responsible for loading
    Resolvers and Hook classes and adding them as constructors to the PyYAML
    parser.

    :param sceptre_dir: The absolute path to the Sceptre directory.
    :type sceptre_dir: str
    """

    def __init__(self, sceptre_dir, variables=None):
        self.logger = logging.getLogger(__name__)

        self.sceptre_dir = sceptre_dir

        # Check is valid sceptre project folder
        self.config_folder = path.join(self.sceptre_dir, "config")
        self._check_valid_sceptre_dir(self.config_folder)

        # Add Resolver and Hook classes to PyYAML loader
        self._add_yaml_constructors(
            ["sceptre.hooks", "sceptre.resolvers"]
        )

        if not variables:
            variables = {}

        self.templating_vars = {"var": variables}

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

    def read(self, rel_path, base_config=None):
        """
        Reads in configuration from yaml files within the Sceptre project
        folder.

        :param rel_path: Relative path to config to read.
        :type rel_path: str
        :param base_config: Base config to provide defaults.
        :type base_config: dict
        :returns: Config read from config files.
        :rtype: dict
        """
        self.logger.debug("Reading in '%s' files...", rel_path)
        directory_path, filename = path.split(rel_path)
        abs_path = path.join(self.config_folder, rel_path)

        # Adding properties from class
        config = {
            "sceptre_dir": self.sceptre_dir,
            "stack_group_path": directory_path
        }

        # Adding defaults from base config.
        if base_config:
            config.update(base_config)

        # Check is file exists, but ignore config.yaml as can be inherited.
        if not path.isfile(abs_path) and not filename.endswith("config.yaml"):
            raise ConfigFileNotFoundError(
                "Config file \"{0}\" not found.".format(rel_path)
            )

        # Parse and read in the config files.
        config.update(self._recursive_read(directory_path, filename))
        self._check_version(config)

        self.logger.debug("Config: %s", config)
        return config

    def _recursive_read(self, directory_path, filename):
        """
        Traverses the directory_path, from top to bottom, reading in all
        relevant config files. If config items appear in files lower down the
        stack_group tree, they overwrite items from further up.

        :param directory_path: Relative directory path to config to read.
        :type directory_path: str
        :param filename: Base config to provide defaults.
        :type filename: dict
        :returns: Representation of inherited config.
        :rtype: dict
        """

        parent_directory = path.split(directory_path)[0]

        # Base condition for recursion
        config = {}

        if directory_path:
            config = self._recursive_read(parent_directory, filename)

        # Read config file and overwrite inherited properties
        child_config = self._read(directory_path, filename) or {}
        config.update(child_config)

        return config

    def _read(self, directory_path, basename):
        """
        Traverses the directory_path, from top to bottom, reading in all
        relevant config files. If config items appear in files lower down the
        stack_group tree, they overwrite items from further up.

        :param directory_path: Relative directory path to config to read.
        :type directory_path: str
        :param filename: Base config to provide defaults.
        :type filename: dict
        :returns: Representation of inherited config.
        :rtype: dict
        """
        abs_directory_path = path.join(self.config_folder, directory_path)
        if path.isfile(path.join(abs_directory_path, basename)):
            stack_group = jinja2.Environment(
                loader=jinja2.FileSystemLoader(abs_directory_path),
                undefined=jinja2.StrictUndefined
            )
            template = stack_group.get_template(basename)
            rendered_template = template.render(
                environment_variable=environ,
                stack_group_path=directory_path.split("/"),
                **self.templating_vars
            )

            config = yaml.safe_load(rendered_template)
            return config

    @staticmethod
    def _check_valid_sceptre_dir(config_path):
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
        Raises a VersionIncompatibleException when the current sceptre version
        does not comply with the configured version requirement.

        :raises: sceptre.exceptions.VersionIncompatibleException
        """
        sceptre_version = __version__
        if 'require_version' in config:
            require_version = config['require_version']
            if Version(sceptre_version) not in SpecifierSet(require_version):
                raise VersionIncompatibleError(
                    "Current sceptre version ({0}) does not meet version "
                    "requirements: {1}".format(
                        sceptre_version, require_version
                    )
                )

    @staticmethod
    def _collect_s3_details(stack_name, config):
        """
        Collects and constructs details for where to store the template in S3.

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
                stack_name, "{time_stamp}.json".format(
                    time_stamp=datetime.datetime.utcnow().strftime(
                        "%Y-%m-%d-%H-%M-%S-%fZ"
                    )
                )
            ])

            if "template_key_prefix" in config:
                prefix = config["template_key_prefix"]
                template_key = "/".join([prefix.strip("/"), template_key])

            s3_details = {
                 "bucket_name": config["template_bucket_name"],
                 "bucket_key": template_key
            }
        return s3_details

    def _construct_stack(self, rel_path, stack_group_config=None):
        """
        Construct a Stack object from a config path and a base config.

        :param rel_path: A relative config file path.
        :type rel_path: str
        :param config: Base config to use as defaults.
        :type config: dict
        :returns: Stack object
        :rtype: sceptre.stack.Stack
        """
        directory, filename = path.split(rel_path)
        if filename != "config.yaml":
            self.templating_vars["stack_group_config"] =\
              stack_group_config
            config = self.read(rel_path, stack_group_config)
            stack_name = path.splitext(rel_path)[0]
            abs_template_path = path.join(
                self.sceptre_dir, config["template_path"]
            )

            s3_details = self._collect_s3_details(
                stack_name, config
            )

            stack = Stack(
                name=stack_name,
                project_code=config["project_code"],
                template_path=abs_template_path,
                region=config["region"],
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
                stack_timeout=config.get("stack_timeout", 0)
            )

            del self.templating_vars["stack_group_config"]
            return stack

    def construct_stack(self, rel_path):
        """
        Construct a Stack object from a config path with the stack_group
        config as the base config.

        :param rel_path: A relative stack config path from the config folder.
        :type rel_path: str
        """
        if not path.isfile(path.join(self.config_folder, rel_path)):
            raise ConfigFileNotFoundError(
                "Config file not found for '{}'".format(rel_path)
            )
        directory = path.split(rel_path)[0]
        stack_group_config = self.read(
            path.join(directory, "config.yaml")
          )
        return self._construct_stack(rel_path, stack_group_config)

    def construct_stack_group(self, rel_path):
        """
        Construct a StackGroup object from a stack_group path
        with all associated sub-stack_groups and stack objects.

        :param rel_path: A relative stack_group path from the config
        folder.
        :type rel_path: str
        """
        if not path.isdir(path.join(self.config_folder, rel_path)):
            raise StackGroupNotFoundError(
                "StackGroup not found for '{}'".format(rel_path)
            )
        stack_group_config = self.read(
            path.join(rel_path, "config.yaml")
          )
        stack_group = StackGroup(rel_path)

        items = glob(
            path.join(self.sceptre_dir, "config", rel_path, "*")
        )

        paths = {
            item: path.relpath(
                item, path.join(self.sceptre_dir, "config")
            )
            for item in items if not item.endswith("config.yaml")
        }

        is_leaf = not any([path.isdir(abs_path) for abs_path in paths.keys()])

        for abs_path, rel_path in paths.items():
            if not is_leaf and path.isdir(abs_path):
                stack_group.sub_stack_groups.append(
                    self.construct_stack_group(rel_path)
                )
            elif is_leaf and path.isfile(abs_path):
                stack = self._construct_stack(
                    rel_path, copy.deepcopy(stack_group_config)
                )
                stack_group.stacks.append(stack)

        return stack_group
