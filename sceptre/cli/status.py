import click

from sceptre.context import SceptreContext
from sceptre.cli.helpers import (
     catch_exceptions,
     get_stack_or_stack_group,
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
                project_path=ctx.obj.get("project_path", None),
                user_variables=ctx.obj.get("user_variables", {}),
                options=ctx.obj.get("options", {}),
                no_colour=ctx.obj.get("no_colour", None),
                output_format=ctx.obj.get("output_format", None)
            )

    stack, stack_group = get_stack_or_stack_group(ctx, path)

    if stack:
        command = 'get_status'
        plan = SceptrePlan(context, command, stack)
        write(plan.execute(), no_colour=context.no_colour)
    elif stack_group:
        command = 'describe'
        plan = SceptrePlan(context, command, stack_group)
        write(plan.execute(), output_format=context.output_format,
              no_colour=context.no_colour)
