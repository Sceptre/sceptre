import click

from sceptre.cli.helpers import (
          catch_exceptions,
          get_stack_or_stack_group,
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

    """
    stack, stack_group = get_stack_or_stack_group(ctx, path)
    output_format = ctx.obj["output_format"]
    action = 'describe_resources'

    if stack:
        plan = SceptrePlan(path, action, stack)
        write(plan.execute(), output_format)
    elif stack_group:
        plan = SceptrePlan(path, action, stack_group)
        write(plan.execute(), output_format)


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

    """
    stack, _ = get_stack_or_stack_group(ctx, path)
    action = 'describe_outputs'
    plan = SceptrePlan(path, action, stack)
    response = plan.execute()

    if export == "envvar":
        write("\n".join(
            [
                "export SCEPTRE_{0}={1}".format(
                    output["OutputKey"], output["OutputValue"]
                )
                for output in response
            ]
        ))
    else:
        write(response, ctx.obj["output_format"])


@list_group.command(name="change-sets")
@click.argument("path")
@click.pass_context
@catch_exceptions
def list_change_sets(ctx, path):
    """
    List change sets for stack.

    """
    stack, _ = get_stack_or_stack_group(ctx, path)
    action = 'list_change_sets'
    plan = SceptrePlan(path, action, stack)
    response = plan.execute()

    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        del response['ResponseMetadata']
    write(response, ctx.obj["output_format"])
