import click

from sceptre.cli.helpers import catch_exceptions, get_stack_or_group
from sceptre.cli.helpers import confirmation
from sceptre.stack_status import StackStatus


@click.command(name="launch")
@click.argument("path")
@click.option(
    "-y", "--yes", is_flag=True, help="Assume yes to all questions."
)
@click.pass_context
@catch_exceptions
def launch_command(ctx, path, yes):
    """
    Launch a stack or stack_group.

    Launch a stack or stack_group for a given config PATH.
    """
    action = "launch"

    stack, group = get_stack_or_group(ctx, path)

    if stack:
        confirmation(action, yes, stack=path)
        response = stack.launch()
        if response != StackStatus.COMPLETE:
            exit(1)
    elif group:
        confirmation(action, yes, stack_group=path)
        response = group.launch()
        if not all(
            status == StackStatus.COMPLETE for status in response.values()
        ):
            exit(1)
