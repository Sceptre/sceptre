import click

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
    output_format = ctx.obj["output_format"]
    no_colour = ctx.obj["no_colour"]

    stack, stack_group = get_stack_or_stack_group(ctx, path)

    if stack:
        command = 'get_status'
        plan = SceptrePlan(path, command, stack)
        write(plan.execute(), no_colour=no_colour)
    elif stack_group:
        command = 'describe'
        plan = SceptrePlan(path, command, stack_group)
        write(plan.execute(), output_format=output_format,
              no_colour=no_colour)
