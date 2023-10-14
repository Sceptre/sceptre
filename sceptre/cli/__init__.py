# -*- coding: utf-8 -*-

"""
sceptre.cli

This module implements Sceptre's CLI, and should not be directly imported.
"""

import os

import click
import colorama

from sceptre import __version__
from sceptre.cli.create import create_command
from sceptre.cli.delete import delete_command
from sceptre.cli.describe import describe_group
from sceptre.cli.diff import diff_command
from sceptre.cli.drift import drift_group
from sceptre.cli.dump import dump_group
from sceptre.cli.execute import execute_command
from sceptre.cli.helpers import catch_exceptions, setup_vars
from sceptre.cli.launch import launch_command
from sceptre.cli.list import list_group
from sceptre.cli.new import new_group
from sceptre.cli.policy import set_policy_command
from sceptre.cli.prune import prune_command
from sceptre.cli.status import status_command
from sceptre.cli.template import (
    validate_command,
    generate_command,
    estimate_cost_command,
    fetch_remote_template_command,
)
from sceptre.cli.update import update_command


@click.group()
@click.version_option(version=__version__, prog_name="Sceptre")
@click.option("--debug", is_flag=True, help="Turn on debug logging.")
@click.option("--dir", "directory", help="Specify sceptre directory.")
@click.option(
    "--output",
    type=click.Choice(["text", "yaml", "json"]),
    default="text",
    help="The formatting style for command output.",
)
@click.option("--no-colour", is_flag=True, help="Turn off output colouring.")
@click.option(
    "--var",
    multiple=True,
    help="A variable to replace the value of an item in config file.",
)
@click.option(
    "--var-file",
    multiple=True,
    type=click.File("rb"),
    help="A YAML file of variables to replace the values of items in config files.",
)
@click.option(
    "--ignore-dependencies",
    is_flag=True,
    help="Ignore dependencies when executing command.",
)
@click.option(
    "--merge-vars",
    is_flag=True,
    default=False,
    help="Merge variables from successive --vars and var files",
)
@click.pass_context
@catch_exceptions
def cli(
    ctx,
    debug,
    directory,
    output,
    no_colour,
    var,
    var_file,
    ignore_dependencies,
    merge_vars,
):
    """
    Sceptre is a tool to manage your cloud native infrastructure deployments.
    """
    colorama.init()
    ctx.obj = {
        "user_variables": setup_vars(var_file, var, merge_vars, debug, no_colour),
        "output_format": output,
        "no_colour": no_colour,
        "ignore_dependencies": ignore_dependencies,
        "project_path": directory if directory else os.getcwd(),
    }


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
cli.add_command(dump_group)
cli.add_command(describe_group)
cli.add_command(fetch_remote_template_command)
cli.add_command(diff_command)
cli.add_command(drift_group)
cli.add_command(prune_command)
