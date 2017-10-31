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

from sceptre.cli import init, create, update, delete, launch, execute, template
from sceptre.cli import describe, status, policy
from helpers import setup_logging
from sceptre import __version__


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

cli.add_command(init.init_group)
cli.add_command(create.create)
cli.add_command(update.update)
cli.add_command(delete.delete)
cli.add_command(launch.launch)
cli.add_command(execute.execute)
cli.add_command(template.validate)
cli.add_command(template.generate)
cli.add_command(policy.set_policy)
cli.add_command(status.status)
cli.add_command(describe.list_group)
cli.add_command(describe.describe_group)
