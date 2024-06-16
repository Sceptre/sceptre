# -*- coding: utf-8 -*-

"""
sceptre.context

This module implements the SceptreContext class which holds details about the
paths used in a Sceptre project.
"""
from copy import deepcopy
from os import path

from sceptre.helpers import normalise_path


class SceptreContext(object):
    """
    SceptreContext is a place that holds data that is relevant to the
    project, including references to the project paths such as the path to your
    Sceptre project, templates path, config path, and the default names for
    your configuration files.

    :param project_path: Absolute path to the base sceptre project folder
    :type project_path: str

    :param command_path: The relative path to either StackGroup or Stack.
    :type command_path: str

    :param user_variables: Used to replace the value of anyvitem in a Config\
            file with a value defined by the CLI flag or in a YAML variable\
            file
    :type user_variables: dict

    :param options: The options specified in by the CLI command
    :type options: dict

    :param output_format: Specify the output format. Available formats:\
            [yaml, json]
    :type output_format: str

    :param no_colour: Specify whether colouring should be used in the CLI\
            output
    :type no_colour: bool

    :param full_scan: Specify whether folder scan the config files\
            True for scan all the config files and False for scan only in the command path
    :type full_scan: bool
    """

    def __init__(
        self,
        project_path,
        command_path,
        command_params=None,
        user_variables=None,
        options=None,
        output_format=None,
        no_colour=False,
        ignore_dependencies=False,
        full_scan=False,
    ):
        # project_path: absolute path to the base sceptre project folder
        # e.g. absolute_path/to/sceptre_directory
        self.project_path = path.abspath(normalise_path(project_path))

        # config_path: holds the project stack_groups
        # e.g {project_path}/config
        self.config_path = "config"  # user definable later in v2

        # command_path path to either stack group or stack
        # e.g. {project_path/config_path}/command_path
        self.command_path = normalise_path(command_path)

        self.normal_command_path = normalise_path(command_path)

        # the sceptre command parameters (e.g. sceptre launch <command params>)
        self.command_params = command_params or {}

        # config_file: stack group config. User definable later in v2
        # e.g. {project_path/config/command_path}/config_file
        self.config_file = "config.yaml"

        # templates_path: holds tempaltes. User definable later in v2
        # e.g. {project_path/}templates
        self.templates_path = "templates"

        self.user_variables = user_variables if user_variables else {}
        self.user_variables = user_variables if user_variables is not None else {}
        self.options = options if options else {}
        self.output_format = output_format if output_format else ""
        self.no_colour = no_colour if no_colour is True else False
        self.ignore_dependencies = (
            ignore_dependencies if ignore_dependencies is True else False
        )
        self.full_scan = full_scan if full_scan is True else False

    def full_config_path(self):
        """
        Returns the config path in the format: ``project_path/config_path``.

        :returns: The absolute path to the config directory
        :rtype: str
        """
        return path.join(self.project_path, self.config_path)

    def full_command_path(self):
        """
        Returns the command path in the format:
        ``project_path/config_path/command_path``.

        :returns: The absolute path to the path that will be executed
        :rtype: str
        """
        return path.join(self.project_path, self.config_path, self.command_path)

    def full_templates_path(self):
        """
        Returns the templates path in the format: project_path/templates_path.

        :returns: The absolute path to the  templates directory
        :rtype: str
        """
        return path.join(self.project_path, self.templates_path)

    def command_path_is_stack(self):
        """
        Returns True if the command path is a file.

        :returns: True if the command path is a file
        :rtype: bool
        """
        return path.isfile(
            path.join(self.project_path, self.config_path, self.command_path)
        )

    def clone(self) -> "SceptreContext":
        """Creates a new, deep clone of the context with all the same values."""
        new = type(self).__new__(type(self))
        new.__dict__.update(deepcopy(self.__dict__))
        return new
