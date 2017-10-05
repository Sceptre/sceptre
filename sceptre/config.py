# -*- coding: utf-8 -*-

"""
sceptre.config

This module implements a Config class, which stores a stack or environment's
configuration.
"""

import logging
import os
import yaml
import collections

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from . import __version__
from .exceptions import ConfigItemNotFoundError
from .exceptions import EnvironmentPathNotFoundError
from .exceptions import VersionIncompatibleError
from .hooks import Hook
from .resolvers import Resolver
from .helpers import get_subclasses

ConfigAttributes = collections.namedtuple("Attributes", "required optional")

ENVIRONMENT_CONFIG_ATTRIBUTES = ConfigAttributes(
    {
        "project_code",
        "region"
    },
    {
        "iam_role",
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
        "dependencies",
        "hooks",
        "parameters",
        "protect",
        "sceptre_user_data",
        "stack_name",
        "stack_tags",
        "role_arn"
    }
)


class Config(dict):
    """
    Config stores the configuration read in from the YAML files. Config
    inherits from dict, and so configuration data can be accessed from Config
    as if Config were a dict. Config implements read(), a method to read in
    config from the ``<base_file_name>.yaml`` files along the
    ``environment_path`` from ``sceptre_dir``.

    :param sceptre_dir: The absolute path to the Sceptre directory.
    :type project dir: str
    :param environment_path: The name of the environment.
    :type environment_path: str
    :param base_file_name: The basename of the file to read in \
        (e.g. "config", "vpc")
    :type base_file_name: str
    """

    def __init__(self, sceptre_dir, environment_path, base_file_name):
        self.logger = logging.getLogger(__name__)

        self.sceptre_dir = sceptre_dir
        self.environment_path = environment_path
        self.name = base_file_name
        self["dependencies"] = []

        self._check_env_path_exists(os.path.join(
            self.sceptre_dir, "config", self.environment_path
        ))

        super(Config, self).__init__(self)

    @classmethod
    def with_yaml_constructors(
            cls, sceptre_dir, environment_path, base_file_name,
            environment_config, connection_manager
    ):
        """
        Initialises a Config object with additional PyYAML constructor classes.

        Creates a Config object and adds PyYAML constructor meta-classes.
        Additional constructors are added to transform YAML nodes for any
        library or external Resolvers and Hooks.

        :param sceptre_dir: The absolute path to the Sceptre directory.
        :type project dir: str
        :param environment_path: The name of the environment.
        :type environment_path: str
        :param base_file_name: The basename of the file to read in \
            (e.g. "config", "vpc")
        :type base_file_name: str
        :param environment_config: The stack's environment's config.
        :type environment_config: sceptre.config.Config
        :param connection_manager: A ConnectionManager used to make Boto3
            calls.
        :type connection_manager: sceptre.connection_manager.ConnectionManager
        """
        obj = cls(sceptre_dir, environment_path, base_file_name)
        obj.add_resolver_constructors(
            environment_config, connection_manager)
        obj.add_hook_constructors(
            environment_config, connection_manager)
        return obj

    def __getitem__(self, item):
        """
        Makes a call to dict's __getitem__. If the item isn't in the dict,
        catch the KeyError raised, and raise a ConfigItemNotFoundException,
        which adds more detail to the exception.

        :param item: The key of an item in the dict to return.
        :type item: Any hashable type
        :returns: The value of the config item keyed by ``item``.
        :rtype: obj
        :raises: sceptre.exceptions.ConfigItemNotFoundException
        """
        try:
            return super(Config, self).__getitem__(item)
        except KeyError:
            raise ConfigItemNotFoundError(
                "'{0}' was not found in any of the {1}.yaml files.".format(
                    item, self.name
                )
            )

    def read(self, user_variables=None, environment_config=None):
        """
        Reads in configuration from files.

        Traverses the environment path, from top to bottom, reading in all
        relevant config files. If config items appear in files lower down the
        environment tree, they overwrite items from further up. Jinja2 is used
        to template in variables from user_variables, environment variables,
        and the segments of the environment path.

        :param user_variables: A dict of key value pairs to be supplied to \
        the config file via Jinja2 templating.
        :type user_variables: dict
        """
        path = os.path.join("config", self.environment_path)
        file_name = ".".join([self.name, "yaml"])

        self.logger.debug("Reading in '%s' files...", file_name)

        def get_config(path):
            """
            Recursively reads in config files in nested subfolders.
            """
            if not path:
                return {}
            else:
                directory_path = os.path.join(self.sceptre_dir, path)
                config = {}
                if os.path.isfile(os.path.join(directory_path, file_name)):
                    env = Environment(
                        loader=FileSystemLoader(directory_path),
                        undefined=StrictUndefined
                    )
                    template = env.get_template(file_name)
                    rendered_template = template.render(
                        environment_variable=os.environ,
                        var=user_variables,
                        environment_path=self.environment_path.split("/"),
                        environment_config=environment_config
                    )

                    yaml_data = yaml.safe_load(rendered_template)
                    if yaml_data is not None:
                        config = yaml_data
                cascaded_config = get_config(os.path.dirname(path))
                cascaded_config.update(config)
                return cascaded_config

        config = get_config(path)

        self.update(config)

        self._check_version()

        self.logger.debug("Config: %s", self)

    @staticmethod
    def _check_env_path_exists(path):
        """
        Raises an EnvironmentPathNotFoundError if ``path`` is not a directory.

        :param path: A directory path.
        :type path: str
        :raises: sceptre.exceptions.EnvironmentPathNotFoundError
        """
        if not os.path.isdir(path):
            raise EnvironmentPathNotFoundError(
                "The environment '{0}' does not exist.".format(path)
            )

    def _check_version(self):
        """
        Raises a VersionIncompatibleException when the current sceptre version
        does not comply with the configured version requirement.

        :raises: sceptre.exceptions.VersionIncompatibleException
        """
        sceptre_version = __version__
        if self.name == 'config' and 'require_version' in self:
            require_version = self['require_version']
            if Version(sceptre_version) not in SpecifierSet(require_version):
                raise VersionIncompatibleError(
                    "Current sceptre version ({0}) does not meet version "
                    "requirements: {1}".format(
                        sceptre_version, require_version
                    )
                )

    def add_resolver_constructors(
            self, environment_config, connection_manager
    ):
        """
        Adds PyYAML constructors for all resolver classes found in the
        resolvers folder within Sceptre library and the current Sceptre project
        folder.

        :param environment_config: A environment config.
        :type environment_config: sceptre.config.Config
        :param connection_manager: A connection manager.
        :type connection_manager: sceptre.connection_manager.ConnectionManager
        """
        self.logger.debug("Adding resolver yaml constructors")

        def resolver_constructor_factory(node_class):
            """
            Returns a lambda function that will contruct objects from a
            given node class.

            :param node_class: A resolver class to construct of objects from.
            :type node_class: class
            :returns: A lambda that constructs resolver objects.
            :rtype: func
            """
            return lambda loader, node: node_class(
                loader.construct_scalar(node),
                connection_manager,
                environment_config,
                self
            )  # pragma: no cover

        resolvers_folder = os.path.join(os.path.dirname(__file__), "resolvers")
        self.add_yaml_constructors(
            resolvers_folder, Resolver, resolver_constructor_factory
        )
        external_resolver_folder = os.path.join(self.sceptre_dir, "resolvers")
        self.add_yaml_constructors(
            external_resolver_folder, Resolver, resolver_constructor_factory
        )

    def add_hook_constructors(self, environment_config, connection_manager):
        """
        Adds PyYAML constructors for all hook classes found in the hooks folder
        within Sceptre library and the current Sceptre project folder.

        :param environment_config: A environment config.
        :type environment_config: Config
        :param connection_manager: A connection manager.
        :type connection_manager: ConnectionManager
        """
        self.logger.debug("Adding hook yaml constructors")

        def hook_constructor_factory(node_class):
            """
            This returns a lambda function that will contruct objects from a
            given node class.

            :param node_class: A hook class to construct of objects from.
            :type node_class: class
            :returns: A lambda that constructs hook objects.
            :rtype: func
            """
            return lambda loader, node: node_class(
                loader.construct_scalar(node),
                connection_manager,
                environment_config,
                self
            )  # pragma: no cover

        library_hook_folder = os.path.join(os.path.dirname(__file__), "hooks")
        self.add_yaml_constructors(
            library_hook_folder, Hook, hook_constructor_factory
        )

        project_hook_folder = os.path.join(self.sceptre_dir, "hooks")
        self.add_yaml_constructors(
            project_hook_folder, Hook, hook_constructor_factory
        )

    def add_yaml_constructors(self, base_directory, base_type, factory):
        """
        Adds PyYAML constructors for all classes which inherit from a
        specific base type within a given directory.

        :param base_directory: A path of a directory to search for classes.
        :type base_directory: str
        :param base_type: The base class in which the class must inherit from.
        :type base_type: class
        :param factory: A function to use to construct objects.
        :type factory: function
        """
        classes = get_subclasses(
            directory=base_directory, class_type=base_type
        )

        for node_name, node_class in classes.items():
            node_tag = u'!' + node_name
            yaml.SafeLoader.add_constructor(
                node_tag, factory(node_class)
            )
            self.logger.debug(
                "Added constructor for %s with node tag %s",
                str(node_class), node_tag
            )
