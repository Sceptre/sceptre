# -*- coding: utf-8 -*-

"""
sceptre.cli

This module implements Sceptre's CLI, and should not be directly imported.
"""

import os

import warnings

import click
import colorama
import yaml

from sceptre import __version__
from sceptre.config_reader import ConfigReader
from sceptre.cli.init import init_group
from sceptre.cli.create import create_command
from sceptre.cli.update import update_command
from sceptre.cli.delete import delete_command
from sceptre.cli.launch import launch_command
from sceptre.cli.execute import execute_command
from sceptre.cli.describe import describe_group
from sceptre.cli.list import list_group
from sceptre.cli.policy import set_policy_command
from sceptre.cli.status import status_command
from sceptre.cli.template import validate_command, generate_command
from sceptre.cli.helpers import setup_logging, catch_exceptions


@click.group()
@click.version_option(version=__version__, prog_name="Sceptre")
@click.option("--debug", is_flag=True, help="Turn on debug logging.")
@click.option("--dir", "directory", help="Specify sceptre directory.")
@click.option(
    "--output", type=click.Choice(["yaml", "json"]), default="yaml",
    help="The formatting style for command output.")
@click.option("--no-colour", is_flag=True, help="Turn off output colouring.")
@click.option(
    "--var", multiple=True, help="A variable to template into config files.")
@click.option(
    "--var-file", type=click.File("rb"),
    help="A YAML file of variables to template into config files.")
@click.pass_context
@catch_exceptions
def cli(
        ctx, debug, directory, no_colour, output, var, var_file
):  # pragma: no cover
    """
    Sceptre is a tool to manage your cloud native infrastructure deployments.

    """
    setup_logging(debug, no_colour)
    colorama.init()
    # Enable deprecation warnings
    warnings.simplefilter("always", DeprecationWarning)
    ctx.obj = {
        "options": {},
        "output_format": output,
        "no_colour": no_colour,
        "sceptre_dir": directory if directory else os.getcwd()
    }
    user_variables = {}
    if var_file:
        user_variables.update(yaml.safe_load(var_file.read()))
    if var:
        # --var options overwrite --var-file options
        for variable in var:
            variable_key, variable_value = variable.split("=")
            user_variables.update({variable_key: variable_value})
    if user_variables:
        ctx.obj["options"]["user_variables"] = user_variables
    ctx.obj["config_reader"] = ConfigReader(
        ctx.obj["sceptre_dir"], ctx.obj["options"]
    )


cli.add_command(init_group)
cli.add_command(create_command)
cli.add_command(update_command)
cli.add_command(delete_command)
cli.add_command(launch_command)
cli.add_command(execute_command)
cli.add_command(validate_command)
cli.add_command(generate_command)
cli.add_command(set_policy_command)
cli.add_command(status_command)
cli.add_command(list_group)
cli.add_command(describe_group)
