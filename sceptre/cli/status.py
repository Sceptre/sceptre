import click

from sceptre.context import SceptreContext
from sceptre.cli.helpers import (
     catch_exceptions,
     write
    )
from sceptre.plan.plan import SceptrePlan


@click.command(name="status")
@click.argument("path")
@click.pass_context
@catch_exceptions
def status_command(ctx, path):
    """
    Print status of stack or stack_group.

    Prints the stack status or the status of the stacks within a
    stack_group for a given config PATH.
    """
    context = SceptreContext(
                command_path=path,
                project_path=ctx.obj.get("project_path"),
                user_variables=ctx.obj.get("user_variables"),
                options=ctx.obj.get("options"),
                no_colour=ctx.obj.get("no_colour"),
                output_format=ctx.obj.get("output_format")
            )

    plan = SceptrePlan(context)

    if len(plan.stack_group.stacks) == 1:
        plan.get_status()
        write(plan.responses[0], no_colour=context.no_colour)
    else:
        plan.describe()
        write(plan.responses, output_format=context.output_format,
              no_colour=context.no_colour)
