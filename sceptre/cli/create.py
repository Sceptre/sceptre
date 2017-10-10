import click

from helpers import catch_exceptions, get_stack
from sceptre.stack_status import StackStatus


@click.command(name="create")
@click.argument("path")
@click.argument("change-set-name", required=False)
@click.pass_context
@catch_exceptions
def create(ctx, path, change_set_name):
    """
    Creates a stack or a change set.

    Creates a stack for a given config PATH. Or if CHANGE_SET_NAME is specified
    creates a change set for stack in PATH.
    """
    stack = get_stack(ctx, path)

    if change_set_name:
        stack.create_change_set(change_set_name)
    else:
        response = stack.create()
        if response != StackStatus.COMPLETE:
            exit(1)
