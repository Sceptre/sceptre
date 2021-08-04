import click

from sceptre.context import SceptreContext
from sceptre.cli.helpers import (
    catch_exceptions,
    simplify_change_set_description,
    write
)
from sceptre.plan.plan import SceptrePlan


@click.group(name="describe")
@click.pass_context
def describe_group(ctx):
    """
    Commands for describing attributes of stacks.
    """
    pass


@describe_group.command(name="change-set")
@click.argument("path")
@click.argument("change-set-name")
@click.option(
    "-v", "--verbose", is_flag=True, help="Display verbose output."
)
@click.pass_context
@catch_exceptions
def describe_change_set(ctx, path, change_set_name, verbose):
    """
    Describes the change set.
    \f

    :param path: Path to execute the command on.
    :type path: str
    :param change_set_name: Name of the Change Set to use.
    :type change_set_name: str
    :param verbose: A flag to display verbose output.
    :type verbose: bool
    """
    context = SceptreContext(
        command_path=path,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        output_format=ctx.obj.get("output_format"),
        no_colour=ctx.obj.get("no_colour"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies")
    )

    plan = SceptrePlan(context)

    responses = plan.describe_change_set(change_set_name)
    for response in responses.values():
        description = response
        if not verbose:
            description = simplify_change_set_description(description)
        write(description, context.output_format, context.no_colour)


@describe_group.command(name="policy")
@click.argument("path")
@click.pass_context
@catch_exceptions
def describe_policy(ctx, path):
    """
    Displays the stack policy used.
    \f

    :param path: Path to execute the command on.
    :type path: str
    """
    context = SceptreContext(
        command_path=path,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        output_format=ctx.obj.get("output_format"),
        no_colour=ctx.obj.get("no_colour"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies")
    )

    plan = SceptrePlan(context)
    responses = plan.get_policy()
    for response in responses.values():
        write(
            response,
            context.output_format,
            context.no_colour
        )
