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
from sceptre.cli.new import new_group
from sceptre.cli.create import create_command
from sceptre.cli.update import update_command
from sceptre.cli.delete import delete_command
from sceptre.cli.launch import launch_command
from sceptre.cli.execute import execute_command
from sceptre.cli.describe import describe_group
from sceptre.cli.list import list_group
from sceptre.cli.policy import set_policy_command
from sceptre.cli.status import status_command
from sceptre.cli.template import (validate_command, generate_command,
                                  estimate_cost_command)
from sceptre.cli.helpers import setup_logging, catch_exceptions


@click.group()
@click.version_option(version=__version__, prog_name="Sceptre")
@click.option("--debug", is_flag=True, help="Turn on debug logging.")
@click.option("--dir", "directory", help="Specify sceptre directory.")
@click.option(
    "--output", type=click.Choice(["text", "yaml", "json"]), default="text",
    help="The formatting style for command output.")
@click.option("--no-colour", is_flag=True, help="Turn off output colouring.")
@click.option(
    "--var", multiple=True, help="A variable to template into config files.")
@click.option(
    "--var-file", multiple=True, type=click.File("rb"),
    help="A YAML file of variables to template into config files.")
@click.option(
    "--ignore-dependencies", is_flag=True, help="Ignore dependencies when executing command.")
@click.pass_context
@catch_exceptions
def cli(
        ctx, debug, directory, output, no_colour, var, var_file, ignore_dependencies
):
    """
    Sceptre is a tool to manage your cloud native infrastructure deployments.

    """
    logger = setup_logging(debug, no_colour)
    colorama.init()
    # Enable deprecation warnings
    warnings.simplefilter("always", DeprecationWarning)
    ctx.obj = {
        "user_variables": {},
        "output_format": output,
        "no_colour": no_colour,
        "ignore_dependencies": ignore_dependencies,
        "project_path": directory if directory else os.getcwd()
    }
    if var_file:
        for fh in var_file:
            parsed = yaml.safe_load(fh.read())
            ctx.obj.get("user_variables").update(parsed)

            # the rest of this block is for debug purposes only
            existing_keys = set(ctx.obj.get("user_variables").keys())
            new_keys = set(parsed.keys())
            overloaded_keys = existing_keys & new_keys  # intersection
            if overloaded_keys:
                logger.debug(
                    "Duplicate variables encountered: {0}. "
                    "Using values from: {1}."
                    .format(", ".join(overloaded_keys), fh.name)
                )

    if var:
        # --var options overwrite --var-file options
        for variable in var:
            variable_key, variable_value = variable.split("=")
            if variable_key in ctx.obj.get("user_variables"):
                logger.debug(
                    "Duplicate variable encountered: {0}. "
                    "Using value from --var option."
                    .format(variable_key)
                )
            ctx.obj.get("user_variables").update(
                {variable_key: variable_value}
            )


cli.add_command(new_group)
cli.add_command(create_command)
cli.add_command(update_command)
cli.add_command(delete_command)
cli.add_command(launch_command)
cli.add_command(execute_command)
cli.add_command(validate_command)
cli.add_command(estimate_cost_command)
cli.add_command(generate_command)
cli.add_command(set_policy_command)
cli.add_command(status_command)
cli.add_command(list_group)
cli.add_command(describe_group)
