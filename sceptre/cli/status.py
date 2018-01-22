import click

from sceptre.cli.helpers import catch_exceptions, get_stack_or_group, write


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

    stack, group = get_stack_or_group(ctx, path)

    if stack:
        write(stack.get_status(), no_colour=no_colour)
    elif group:
        write(group.describe(), output_format=output_format,
              no_colour=no_colour)
