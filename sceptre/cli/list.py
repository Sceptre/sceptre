import click

from sceptre.context import SceptreContext
from sceptre.cli.helpers import (
    catch_exceptions,
    write
)
from sceptre.plan.plan import SceptrePlan


@click.group(name="list")
def list_group():
    """
    Commands for listing attributes of stacks.

    """
    pass


@list_group.command(name="resources")
@click.argument("path")
@click.pass_context
@catch_exceptions
def list_resources(ctx, path):
    """
    List resources for stack or stack_group.
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
        ignore_dependencies=ctx.obj.get("ignore_dependencies")
    )
    plan = SceptrePlan(context)

    responses = [
        response for response
        in plan.describe_resources().values() if response
    ]

    write(responses, context.output_format)


@list_group.command(name="outputs")
@click.argument("path")
@click.option(
    "-e", "--export", type=click.Choice(["envvar"]),
    help="Specify the export formatting."
)
@click.pass_context
@catch_exceptions
def list_outputs(ctx, path, export):
    """
    List outputs for stack.
    \f

    :param path: Path to execute the command on.
    :type path: str
    :param export: Specify the export formatting.
    :type export: str
   """
    context = SceptreContext(
        command_path=path,
        project_path=ctx.obj.get("project_path", None),
        user_variables=ctx.obj.get("user_variables", {}),
        options=ctx.obj.get("options", {}),
        output_format=ctx.obj.get("output_format"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies")
    )

    plan = SceptrePlan(context)
    responses = [
        response for response
        in plan.describe_outputs().values() if response
    ]

    if export == "envvar":
        for response in responses:
            for stack in response.values():
                for output in stack:
                    write("export SCEPTRE_{0}='{1}'".format(
                                output.get("OutputKey"),
                                output.get("OutputValue")
                            ), 'str')
    else:
        write(responses, context.output_format)


@list_group.command(name="change-sets")
@click.argument("path")
@click.pass_context
@catch_exceptions
def list_change_sets(ctx, path):
    """
    List change sets for stack.
    \f

    :param path: Path to execute the command on.
    :type path: str
    """
    context = SceptreContext(
        command_path=path,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        output_format=ctx.obj.get("output_format"),
        options=ctx.obj.get("options"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies")
    )

    plan = SceptrePlan(context)
    responses = [
        response for response
        in plan.list_change_sets().values() if response
    ]

    for response in responses:
        write(response, context.output_format)
