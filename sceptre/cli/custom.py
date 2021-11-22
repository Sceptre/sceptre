import click
import json

from sceptre.context import SceptreContext
from sceptre.cli.helpers import (
    catch_exceptions,
    write
)
from sceptre.plan.plan import SceptrePlan


@click.command(name="stack-name", short_help="Reveal the stack name or names.")
@click.argument("path")
@click.option(
    "-P", "--print-name", is_flag=True, default=False,
    help="Also print sceptre's name for this stack.",
)
@click.pass_context
@catch_exceptions
def stack_name_command(ctx, path, print_name):
    """
    Show the stack names of all stacks.
    \f

    :param path: The path to execute the command on.
    :type path: str
    :param print_name: Also print the internal stack name.
    :type print_name: bool
    """
    context = SceptreContext(
        command_path=path,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies")
    )

    plan = SceptrePlan(context)
    responses = plan.stack_name(print_name)

    for response in responses.values():
        write(response, context.output_format)


@click.command(name="detect-stack-drift", short_help="Detects stack drift on running stacks.")
@click.argument("path")
@click.pass_context
@catch_exceptions
def detect_stack_drift_command(ctx, path):
    """
    Detect stack drift on running stacks.
    \f

    :param path: The path to execute the command on.
    :type path: str
    """
    context = SceptreContext(
        command_path=path,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies")
    )

    plan = SceptrePlan(context)
    responses = plan.detect_stack_drift()
    output = "\n".join([
        json.dumps({stack_name: response}, sort_keys=True, indent=2, default=str)
        for stack_name, response in responses.values()
    ])
    write(output, context.output_format)
